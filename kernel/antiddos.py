import re
from kernel.aes import AESModeOfOperation as aes
def toStr(n, base):
    convert = "0123456789ABCDEF"
    if n < base:
        return convert[n]
    else:
        return toStr(n//base, base) + convert[n%base]

def toNumbers(inp):
    return [int(i, 16) for i in re.findall(r"(..)", inp)]

def toHex(arg):
    outString = ""
    for v in arg:
        outString += ('0' if v < 16 else '') + toStr(v, 16)
    return outString.lower()

def get(index):

    hashez = re.findall(r'"(\w+)"', index)

    a = toNumbers(hashez[0])
    b = toNumbers(hashez[1])
    c = toNumbers(hashez[2])

    cookie_value = toHex(aes().decrypt(c, 2, a, b))

    return cookie_value