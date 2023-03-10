from kernel.log import Log
import xmltodict, requests, re, config, html, time, sys
from bs4 import BeautifulSoup as bs
import kernel.antiddos
from kernel.vk import VK
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from constants import OBSCENES
from better_profanity import profanity
profanity.add_censor_words(OBSCENES)

log = Log("[Parser]").log
DOMAIN = "gta-trinity.com"
URL = f'https://{DOMAIN}/forum/'

class Forum:
    session : requests.Session
    def __init__(self, useproxy = True) -> None:
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.NAME})
        if useproxy:
            self.session.proxies = {'http': 'socks5h://127.0.0.1:9050','https': 'socks5h://127.0.0.1:9050'}
        self.connect()

    def connect(self):
        index = self.session.get(URL).text
        log("Success connection")
        ddos_code = kernel.antiddos.get(index)
        cookies = dict(
            name='REACTLABSPROTECTION',
            value=ddos_code,
            path='/',
            domain=DOMAIN,
            expires=2145916555,
            rest = {'hostOnly':True}
        )
        self.session.cookies.set(**cookies)
        log("Anti-DDOS code set")
    
    def getPage(self, url) -> requests.Response:
        try:
            return self.session.get(url)
        except:
            log("Ошибка получения ссылки", url)
            return None
    
    def getXmlPage(self):
        try:
            return self.session.get(URL+"index.php?/discover/8.xml/", timeout=20)
        except:
            log("Ошибка получения XML")
            return None

class Post:
    hat : str = None
    tag : str = None
    title : str = None
    id : str = None
    attached_images : list = None
    subforums : list = None 
    text : str = None
    link : str = None

    class Image:
        img = ""
        def __init__(self, img):
            self.img = img
        def content(self):
            if "http" in self.img:
                return requests.get(self.img, stream=True).content
            else: return open(self.img, 'rb')

    def __init__(self, id) -> None:
        self.id = id
        self.hat = ""
        self.tag = ""
        self.title = ""
        self.attached_images = []
        self.subforum = []
        self.text = ""
        self.link = ""

    def getAttachment(self):
        for i in range(len(self.subforums)-1, 0, -1):
            title = self.subforums[i].lower()
            if "жалобы на хелперов" in title:
                return "attachments/helper_report.jpg"
            elif "претензии к работе администраторов" in title:
                return "attachments/admin_report.jpg"
            elif "на лидеров фракций и банд" in title:
                return "attachments/leader_report.jpg"
            elif "новый лидер" in title:
                return "attachments/new_leader.jpg"
            elif "банды" in title:
                return "attachments/gang_news.jpg"
            elif "байкерские клубы" in title:
                return "attachments/biker_news.jpg"
            elif "мафии" in title:
                return "attachments/maf_news.jpg"
            elif "правительство" in title:
                return "attachments/polit_news.jpg"
            elif "передачу постов" in title:
                return None
            elif "поощрения лидерам" in title:
                return ["attachments/encouragement.jpg", "attachments/encouragement_2.jpg"]
            elif "выговоры лидеров" in title:
                return "attachments/leader_reb.jpg"
        return "attachments/fract_news.jpg"
    
    def remove_obscenes(self, text: str):
        return profanity.censor(text)
    
    def post_is_exist(self, vk: VK, text: str):
        wall_get_data =  {
            "owner_id": 0-config.POST_GROUP_ID,
            "count": 3,
        }
        result = vk.api("wall.get", **wall_get_data)

        if not result:
            return False, 0
        
        for post in result['items']:
            percent = fuzz.ratio(post['text'], text)
            if percent > 74:
                return True, percent
            
        return False, 0
                

    def vkupload(self, vk : VK) -> bool:
        if "-test" in sys.argv:
            vk.api("messages.send", peer_id= config.PROD_CONV_PEER, message = f"[TESTING]\nОбнаружен и готов к публикации пост.")
            return True
        if len(self.attached_images) != 0:
            photo = ""
            for img in self.attached_images:
                photo += self.upload_photo(img, vk) + ","
        elif self.hat != "":
            photo = self.upload_photo(self.hat, vk)
        else:
            att = self.getAttachment()
            if type(att) == list:
                photos = []
                for a in att:
                    photos.append(self.upload_photo(a, vk))
                photo = ','.join(photos)
            else:
                photo = self.upload_photo(att, vk)
                
        self.text = self.remove_obscenes(self.text)
        
        wall_post_data =  {
            "owner_id": 0-config.POST_GROUP_ID,
            "from_group": 1,
            "message": f"{self.tag}\n{self.title}\n\n{self.text}",
            "copyright": self.link
        }
        
        is_exist, percent = self.post_is_exist(vk, wall_post_data["message"])
        if is_exist:
            vk.api("messages.send", peer_id= config.PROD_CONV_PEER, message = f"{str('-'*32)}\nПолучен пост на {int(percent)}% похожий на тот что уже есть в группе.\n\n{self.link}\n{str('-'*32)}")
            log("Такой пост уже есть в группе!")
            return True
        
        if len(self.text) < 250:
            if not self.title == 'Заявки на передачу постов лидера фракций, банд, мафий и байкерских клубов':
                wall_post_data["publish_date"] = int(time.time())+24*3600
            
        if photo: wall_post_data["attachments"] = photo

        posted = vk.api("wall.post", **wall_post_data)
        if posted:
            if len(self.text) < 250:
                vk.api("messages.send", peer_id= config.PROD_CONV_PEER, message = f"{str('-'*32)}\nВ отложке новый пост, проверьте вручную:\n\n{self.tag}\n{self.title}\n\n{self.text}\n\n{self.link}\n{str('-'*32)}")
            else:
                vk.api("messages.send", peer_id= config.PROD_CONV_PEER, message = f"{str('-'*32)}\nСкорее всего пост нормальный и запощен автоматически:\n\n{self.tag}\n{self.title}\n\n{self.link}\n{str('-'*32)}")
            log("Posted \""+self.title+"\" post_id = "+str(self.id))
            return True
        else:
            vk.api("messages.send", peer_id= config.PROD_CONV_PEER, message = f"Ошибка wall.post")
            log("Ошибка поста")
            return False

    def upload_photo(self, img, vk : VK):
        if not img: return None
        img = self.Image(img)
        r = vk.api("photos.getWallUploadServer", peer_id=config.POST_GROUP_ID)
        r = requests.post(r['upload_url'],files={'photo':('photo.png', img.content(),'image/png')}).json()
        r = vk.api("photos.saveWallPhoto", photo= r['photo'], server= r['server'], hash = r['hash'])
        return f"photo{r[0]['owner_id']}_{r[0]['id']}" if r else ""

class ForumException(Exception):
    pass

class Parser:
    exclude : list
    trigger : list
    posted_ids : list
    forum : Forum

    def __init__(self, forum : Forum, trigger_names = [], exclude_names = [], posted = []) -> None:
        self.forum = forum
        self.exclude = exclude_names
        self.trigger = trigger_names
        self.posted_ids = posted

    def updateForum(self, newforum):
        self.forum = newforum

    def search(self):
        html = self.forum.getXmlPage()
        if html:
            return self.process(xmltodict.parse(html.text, encoding="utf-8"))
        else:
            raise ForumException

    def savePostedId(self, id):
        self.posted_ids.append(id)
        if len(self.posted_ids) >= 20:
            self.posted_ids = self.posted_ids[1:]
        open(config.fileposted, "w").write(",".join(self.posted_ids))

    def process(self, xml) -> Post:
        for post in xml['rss']['channel']['item']:

            post_id = re.findall(r't&comment=(\d+)', post['link'])[0]
            title = post['title']

            HasTitle=False
            ExitFlag=False
            for news_alert in self.trigger:
                if not ExitFlag:
                    sub = title.lower().replace(news_alert.lower(), '')
                    if len(sub) != len(title): ExitFlag = True
            for news_name in self.exclude:
                if news_name.lower() in sub:
                    HasTitle = True
            if(not HasTitle): continue

            if str(post_id) in self.posted_ids:
                continue

            log(f"[{post_id}] New post was found", title=title)
            POST = Post(post_id)
            POST.title = title

            if "жалоб" in title.lower() or "претенз" in title.lower():
                POST.tag = "#ccreport"
            else:
                POST.tag = "#ccnews"

            post_html = bs(self.forum.getPage(post['link']).text,'html.parser')
            forum_post = post_html.find('article', {'id': f"elComment_{post_id}"})
            forum_post = forum_post.find('div', class_='ipsType_normal ipsType_richText ipsPadding_bottom ipsContained')

            try:
                for img in forum_post.find_all('img'):
                    if not "emoji" in img['data-src']:
                        POST.attached_images.append(img['data-src'])
                log(f"[{post_id}] Added {len(POST.attached_images)} post photos")
            except: pass
            
            if len(POST.attached_images) == 0:
                log(f"[{post_id}] No post photos found, getting header photo")
                index = bs(self.forum.getPage(re.findall(r"(.+)\?do=findComment&", post['link'])[0]).text,'html.parser')

                forum_post = index.find_all('article')[0]
                forum_post = forum_post.find('div', class_='ipsType_normal ipsType_richText ipsPadding_bottom ipsContained')
                try:
                    POST.hat = forum_post.find_all('img')[0]['data-src']
                    log(f"[{post_id}] Header photo got")
                except:
                    log(f"[{post_id}] No header photo was found")
                    pass

            POST.subforums = []
            nav_bar = post_html.find('nav', class_="ipsBreadcrumb ipsBreadcrumb_top ipsFaded_withHover")
            nav_bar = nav_bar.find('ul', attrs={"data-role": True})
            spans = nav_bar.find_all('span')
            for sp in spans:
                POST.subforums.append(re.sub(r'(\<(/?[^>]+)>)', '', str(sp)))
            POST.subforums.append(title)

            post['description'] = re.sub(r'\t', '', post['description'])
            post['description'] = re.sub(r'\n\s*\n', '\n', post['description'])
            post['description'] = html.unescape(post['description'])
            POST.text = post['description']
            POST.link = post['link']

            return POST

        return None


