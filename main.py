from json import load
from turtle import title
from kernel.vk import VK
from kernel.log import Log
from kernel.parser import Parser, Forum, Post
import os, config

log = Log("[MAIN]").log
posted = [i for i in open(config.fileposted, 'r').read().split(',')]

vk = VK(os.getenv("VK_TOKEN", default=""))
parser = Parser(Forum(False), config.news_alerts, config.news_names, posted=posted)

while True:
    try:
        log("Searching for new post...")
        result = parser.search()
        if result:
            log("Found new post", id=result.id, title=result.title)
            loaded = result.vkupload(vk)
            if loaded:
                log("Uploaded to vk")
                parser.savePostedId(result.id)
            else:
                log("Error while uploading")
        else:
            log("Skipped")
    except Exception as e:
        print(e)
