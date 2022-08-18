import inspect, time, sys

class Log:
    prefix : str
    def __init__(self, prefix = "") -> None:
        self.prefix = prefix

    def getStrTime(self):
        return time.strftime('[%m.%d %H:%M:%S]')

    def log(self, *args, createfile=False, **kwargs):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 3)
        text = ""
        for v in args: text += "{}\t".format(v)
        if kwargs:
            for k in kwargs: text += "{} = {}\t".format(k, kwargs[k])
        text = text[:-1]
        text = f"{self.getStrTime()} {self.prefix} ({calframe[1][3]}:{calframe[1][2]}): "+text
        if "-dev" in sys.argv:
            print(text)
        if createfile:
            open("log.txt", "w")
        open("log.txt", 'a', encoding="utf-8").write(text+"\n")