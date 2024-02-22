import psutil

def memInfo():
    process = psutil.Process()
    mem = int(process.memory_info().rss / 1024)
    print ("\n--- Current memory usage in kbytes: " + str(mem) + "\n")

def dumper(mclass):
    text = ""
    for attr in dir(mclass):
        if not attr.startswith("__"):
            m = getattr(mclass, attr)
            if isinstance(m, int) or isinstance(m, str) or  isinstance(m, list):
                text += (" %s = %r\n" % (attr, m))
    return(text)

