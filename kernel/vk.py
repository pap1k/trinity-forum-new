import requests, time, sys
from random import randint as rand
from kernel.log import Log

CORE_V = 0.3

API_URL = "https://api.vk.com/method/"
API_V = 5.103
MAX_REQUESTS_PER_SEC = 4
REQUEST_DELAY = int(1/MAX_REQUESTS_PER_SEC*1000)
MAX_MESSAGE_LENGTH = 4095

logCore = Log("[VK API / VK]").log
logLP = Log("[VK API / LP]").log

def userToGroupEvent(eId):
    table = {
        4: "message_new",
        5: "message_edit"
    }
    return table[eId] if eId in table else "Unknown"

def time_ms():
    return int(time.time()*1_000)

class VK:
    _lastQTS : float #last query timestamp
    _queue : list
    token : str
    v : float
    lang : str

    def __init__(self, token : str, v = API_V, lang = "ru") -> None:
        self._queue = []
        self._lastQTS = time_ms()
        self.lang = lang
        self.token = token
        self.v = v

    def _queue_push(self, url, data):
        self._queue.append({
            "URL": url,
            "DATA": data
        })
        start_wait = time_ms()
        while time_ms() - self._lastQTS < REQUEST_DELAY:
            time.sleep(0.1)

        #logCore(LQTS=self._lastQTS, CUR=time_ms(), DIFF=time_ms() - self._lastQTS, DELAY_WAS=time_ms()-start_wait)
        
        return self._do_request()

    def _do_request(self, req = None):
        if req: oldreq = req
        else: oldreq = self._queue.pop(0)
        try:
            self._lastQTS = time_ms()
            r = requests.post(oldreq["URL"], data=oldreq["DATA"]).json()
        except requests.exceptions.ConnectionError:
            logCore('Соединение отвалилось, пробуем снова')
            return self._do_request(oldreq)

        if 'error' in r:
            err = r['error']['error_code']
            if err == 6:
                time.sleep(0.5)
                self._do_request(oldreq)
            else:
                logCore("An error: ", r['error']['error_msg'])
            return None 
        else:
            return r['response']

    def _text_split(self, text : str):
        #Делим по \n
        sp = text.split('\n')
        newtxt = [""]
        idx = 0
        for w in sp:
            if len(w) + len(newtxt[idx])+1 > MAX_MESSAGE_LENGTH:
                idx += 1
                newtxt.append("")
            newtxt[idx] += w + '\n'
        if len(newtxt) < len(text)//MAX_MESSAGE_LENGTH+1:
            #Делим по пробелу, если не удалось по \n
            sp = text.split(' ')
            newtxt = [""]
            idx = 0
            for w in sp:
                if len(w) + len(newtxt[idx])+1 > MAX_MESSAGE_LENGTH :
                    idx += 1
                    newtxt.append("")
                newtxt[idx] += w+' '
        return newtxt

                
    def api(self, method, priority = 0, **params):
        params['access_token'] = self.token
        params['v'] = self.v
        params['lang'] = self.lang

        if method == "messages.send":
            params['random_id'] = rand(1000, 100000)
            #Фикс длины сообщения
            if 'message' in params:
                if len(params['message']) > MAX_MESSAGE_LENGTH:
                    texts = self._text_split(params['message'])
                    if len(texts) > 1:
                        for text in texts:
                            newparams = params
                            newparams['message'] = text
                            self.api(method, **newparams)
                        return
        if priority == 1:
            return self._do_request({"URL":API_URL+method, "DATA":params})
        return self._queue_push(API_URL+method, data=params)

class LongPoll:
    key : str
    ts : int
    server : str
    wait : int
    vkInstanse : VK
    doFlag = True
    group_id : int
    listeners : list
    mode : str

    def __init__(self, vk, group_id = 0, wait = 20) -> None:
        if type(vk) == VK:
            self.vkInstanse = vk
        else:
            self.vkInstanse = VK(vk)
        self.listeners = []
        self.group_id = group_id
        self.wait = wait
        self.getServerInfo()

    def getServerInfo(self):
        if self.group_id != 0:
            info = self.vkInstanse.api("groups.getLongPollServer", group_id=self.group_id)
            self.mode = "group"
        else:
            info = self.vkInstanse.api("messages.getLongPollServer")
            self.mode = "user"

        self.key = info['key']
        self.ts = info['ts']
        self.server = info['server'] if "https" in info['server'] else 'https://'+info['server']

    def addListener(self, event, listener):
        self.listeners.append([event, listener])

    def run(self):
        self.doFlag = True
        first = True
        while self.doFlag:
            try:
                if first:
                    logLP("Бот слушает обновления")
                    first = False

                resp = requests.get(f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait={self.wait}").json()
                if 'failed' in resp:
                    if resp['failed'] == 1:
                        self.ts = resp['ts']
                        continue
                    elif resp['failed'] == 2 or resp['failed'] == 3:
                        self.getServerInfo()
                        continue
                    elif resp['filed'] == 4:
                        continue
                    else:
                        logLP("Unknown erorr")
                        self.getServerInfo()
                        continue
                if resp['ts'] != self.ts:
                    self.ts = resp['ts']
                for upd in resp['updates']:
                    for listener in self.listeners:
                        event = upd['type'] if self.mode == "group" else userToGroupEvent(upd[0])
                        if listener[0] == event:
                            # print('Пришло сообщение')
                            if self.mode == "user":
                                #КОСТЫЛЬ ТОЛЬКО НА СООБЩЕНИЯ КОТОРЫЕ ЧЕРЕЗ ЮЗЕР ЛОНГПОЛЛ
                                # try:
                                #     mess = self.vkInstanse.api("messages.getById", message_ids=upd[1])['items'][0]
                                # except IndexError:
                                    # mess = self.vkInstanse.api("messages.getById", message_ids=upd[1])['items'][0]
                                mess = None
                                i = 0
                                while mess == None:
                                    i += 1
                                    items = self.vkInstanse.api("messages.getById", message_ids=upd[1])
                                    try:
                                        mess = items['items'][0]
                                        obj = {'message': mess}
                                    except (IndexError, TypeError, NameError) as e:
                                        logLP(f"Проблема с получением сообщения [{upd[1]}]: {e}")
                                        break
                                    try:
                                        listener[1](obj)
                                    except Exception as e:
                                        logLP(f"Проблема с обработкой сообщения листенером: {e}")
                                        

                                # print(f'Сообщение: {mess}')
                                # threading.Thread(target=listener[1], args=(obj,)).start()
                            else:
                                # threading.Thread(target=listener[1], args=(upd['object'],)).start()
                                listener[1](upd['object'])
                                        
            except KeyboardInterrupt:
                self.stop()
            except requests.exceptions.ConnectionError:
                logLP('Соединение отвалилось, пробуем снова')

            # except Exception as e:
            #     print("Uncatchable exception: ", e)

    def stop(self):
        logLP("Stopping LongPoll")
        self.doFlag = False 