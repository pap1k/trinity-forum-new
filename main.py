from kernel.vk import VK
from kernel.log import Log
from kernel.parser import Parser, Forum, ForumException
import os, config, time

log = Log("[MAIN]").log
posted = [i for i in open(config.fileposted, 'r').read().split(',')]

vk = VK(os.getenv("VK_TOKEN", default=""))
parser = Parser(Forum(False), config.news_alerts, config.news_names, posted=posted)

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
        parser.updateForum(Forum(False))
    except KeyboardInterrupt:
        work = False
