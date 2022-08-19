from email import message
from kernel.vk import VK
from kernel.log import Log
from kernel.parser import Parser, Forum, ForumException
from os.path import exists
import os, config, time, sys

log = Log("[MAIN]").log
if not exists(config.fileposted):
    open(config.fileposted, 'w').close()
posted = [i for i in open(config.fileposted, 'r').read().split(',')]

time_start = time.time()

vk = VK(os.getenv("VK_TOKEN", default=""))
parser = Parser(Forum(), config.news_alerts, config.news_names, posted=posted)

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
            vk.api("messages.send", peer_id=config.PROD_CONV_PEER, message="[TESTING]\nСоединение с форумом потеряно. С момента запуска (последнего обновления): "+str((time.time()-time_start)/60)+" минут")
            time_start = time.time()
        parser.updateForum(Forum())
    except KeyboardInterrupt:
        work = False
    except Exception as e:
        log("Exception handled, exiting")
        work=False
