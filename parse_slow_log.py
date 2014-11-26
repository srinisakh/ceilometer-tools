import sys

TOKEN_LIST = ["Query_time: ", "User@Host: ", "Schema: "]

f = open(sys.argv[1])
for s in f.xreadlines(): 
    res = ""
    for t in TOKEN_LIST:
        i = s.find(t)
        if i == -1:
            value = "NONE"
        else:
            value = s[i+len(t):].split(' ', 1)[0]
        res = res + t + ",\t" + value + ",\t"
    sys.stdout.write(res + s)
