from email import message
from kernel.vk import VK
from kernel.log import Log
from kernel.parser import Parser, Forum, ForumException, Post
from os.path import exists
import os, config, time, sys
from constants import NEWS_ALERTS, NEWS_NAMES

log = Log("[MAIN]").log
if not exists(config.fileposted):
    open(config.fileposted, 'w').close()
posted = [i for i in open(config.fileposted, 'r').read().split(',')]

time_start = time.time()

vk = VK(config.VK_TOKEN)
parser = Parser(Forum(not("-test" in sys.argv)), NEWS_ALERTS, NEWS_NAMES, posted=posted)

log("============================")
log(config.NAME, "STARTED")
log("============================")
if "-test" in sys.argv:
    vk.api("messages.send", peer_id=config.PROD_CONV_PEER, message="[TESTING]\nБот запущен")

if "-test2" in sys.argv:
    result = Post("0")
    result.tag = "#ccnews"
    result.title = "TESTTEST"
    result.subforums = ["Главная","Разделы игровых серверов", "Trinity RPG - 185.169.134.83:7777", "Жалобы и игровые обсуждения","Поощрения лидерам и хелперам за их активность"]
    result.text = "Это тестовый пост. Всем привет."
    result.link = "http://vk.com/id0"

    result.vkupload(vk)

work = True
while work:
    try:
        log("Searching for new post...")
        result = parser.search()
        if result:
            loaded = result.vkupload(vk)
            if loaded:
                log(f"[{result.id}] Uploaded to vk")
                parser.savePostedId(result.id)
            else:
                log("Error while uploading")
        else:
            log(f"Waiting for {config.DELAY} min")
            time.sleep(60*config.DELAY)
    except ForumException:
        log("Forum exception, re-init forum connection")
        if "-test" in sys.argv:
            vk.api("messages.send", peer_id=config.PROD_CONV_PEER, message="[TESTING]\nСоединение с форумом потеряно. С момента запуска (последнего обновления): "+str((time.time()-time_start)//60)+" минут")
            time_start = time.time()
        parser.updateForum(Forum())
    except KeyboardInterrupt:
        work = False
    except Exception as e:
        log(f"Exception handled, exiting: {e}")
        work=False
