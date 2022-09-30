import os
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
fileposted = os.getenv("FILE_POSTED")
POST_GROUP_ID = int(os.getenv("POST_GROUP_ID"))
PROD_CONV_PEER = int(os.getenv("PROD_CONV_PEER")) + 2000000000
DELAY = int(os.getenv("DELAY")) #3 : 28_800 times a day, 5 : ~ 15k-17k
NAME = '[CC]Trinity Parser/v2.4'
