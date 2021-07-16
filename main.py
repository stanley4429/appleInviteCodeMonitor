# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import time
import json
from bs4 import BeautifulSoup
import telegram
from telegram.utils.helpers import DEFAULT_20
from DBHelper import DBHelper
# 要求吗revoke次数
revokeCount = 0
channels = []


# 电报通知
def notify_ending(message, isPin=False):
    with open('./docs/keys.json', 'r') as keys_file:
        k = json.load(keys_file)
        token = k['en_telegram_token']
        chat_id = k['en_telegram_chat_id']
        bot = telegram.Bot(token=token)
        if isPin:
            bot.sendMessage(chat_id=chat_id, text=message, disable_web_page_preview=DEFAULT_20).pin()
        else:
            bot.sendMessage(chat_id=chat_id, text=message, disable_web_page_preview=DEFAULT_20)


# app下载页面
async def newDownTfPage(session, channel):
    try:
        async with session.post("https://api.touronghui.net/front/newDownTfPage?%s" % (time.time()),
                                data={'randStr': channel['c_randStr']}, ssl=False) as resp:
            print("url: ", resp.url)
            print("Status: ", resp.status)
            print("Content-type: ", resp.headers["content-type"])

            html = await resp.json()
            print("Body: ", html)

    except Exception as ex:
        notify_ending(repr(ex))


# 获取邀请码
async def getInvitationCode(session, channel):

    try:
        async with session.post("https://api.touronghui.net/front/getInvitationcode?%s" % (time.time()),
                                data={'randStr': channel['c_randStr']}, ssl=False) as resp:
            try:
                html = await resp.json()
                if int(html['code']) == 1:
                    return html
                else:
                    notify_ending('%s: \n%s\n#请求异常  (code == %s): \n%s'
                                  % (channel['c_name'], channel['c_link'], html['code'], html), isPin=True)
            except Exception as ex:
                notify_ending('%s\n#返回数据异常  %s\n%s' % (channel['c_name'], channel['c_link'], repr(ex)), isPin=True)

    except Exception as ex:
        notify_ending('%s\n#请求异常地址  %s\n%s' % (channel['c_name'], channel['c_link'], repr(ex)), isPin=True)


# 苹果testflight链接邀请
async def appleInvite(session, params, channel):
    url = params["data"]
    global revokeCount
    if url is not None:
        try:
            async with session.get(url, ssl=False) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'lxml')

                try:
                    inviteCode = soup.find('span', attrs={'class': 'bold black'}).string
                    print(inviteCode)
                    notify_ending('%s\n邀请码: %s\n邀请链接：%s' % (channel['c_name'], inviteCode, url))
                except Exception as ex:
                    revokeCount = revokeCount + 1
                    if revokeCount > 5:
                        notify_ending('%s: revokeCount: ', (channel['c_name'], revokeCount))
                    notify_ending('%s\n%s\n#异常信息： \n%s' % (channel['c_name'], url, soup.prettify()), isPin=True)
                finally:
                    print('------------------')
        except Exception as ex:
            notify_ending('%s\n session.geturl %s' % (channel['c_name'], repr(ex)), isPin=True)
    else:
        notify_ending('%s: url异常: %s' % (channel['c_name'], str(params)), isPin=True)


# 主函数
async def main():
    global channels
    with open('./docs/dbConf.json', 'r') as dbConf:
        conf = json.load(dbConf)
        dbHelper = DBHelper(host=conf['jc_host'], port=conf['jc_port'],
                            user=conf['jc_user'], passwd=conf['jc_password'])
        dbHelper.select_db('jcbot')
    # timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession() as session:
        while True:
            # await newDownTfPage(session, {'randStr': '0jo6eu4s6g'})
            sql = "select * from channel"
            data = dbHelper.query_db(sql, state='all')
            if data is None:
                data = channels
            else:
                for dc in data:
                    for cc in channels:
                        if cc['c_name'] == dc['c_name']:
                            if cc['c_link'] != dc['c_link']:
                                notify_ending('%s\n旧链接：\n%s\n新链接：\n%s' % (dc['c_name'], cc['c_link'], dc['c_link']))
                            if int(cc['c_valid']) != int(dc['c_valid']):
                                if int(dc['c_valid']) == 1:
                                    notify_ending('%s\n✅加入检测队列' % (dc['c_name']))
                                else:
                                    notify_ending('%s\n⚠️移除️检测队列' % (dc['c_name']))
                channels = data

            for c in channels:
                if int(c['c_valid']) == 1:
                    params = await getInvitationCode(session, c)
                    if params is not None:
                        await appleInvite(session, params, c)
                    time.sleep(10)

            time.sleep(300)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
