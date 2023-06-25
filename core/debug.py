import psutil

def memInfo():
    process = psutil.Process()
    mem = int(process.memory_info().rss / 1024)
    print ("\n--- Current memory usage in kbytes: " + str(mem) + "\n")


