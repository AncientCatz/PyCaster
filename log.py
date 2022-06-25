import time
from termcolor import colored


_log = []

def Log(msg, evt="info"):
    with open("log/PyCasterServer.log", "r") as f:
        for line in f.readlines():
            _log.append(line.strip())
    m = ""
    if evt == "info":
        m = f'[INF] - {time.ctime()} {msg}'
        return '['+colored("INF", 'green')+'] - ' + colored(time.ctime(), 'magenta', attrs=['underline']) + " "+ colored(msg, color="cyan")

    elif evt == "err":
        m = f'[ERR] - {time.ctime()} {msg}'
        return '['+colored("ERR", 'red')+'] - ' + colored(time.ctime(), 'magenta', attrs=['underline']) + " "+ colored(msg, color="red")
    elif evt == "warn":
        m = f'[WRN] - {time.ctime()} {msg}'
        return '['+colored("WRN", 'yellow')+'] - ' + colored(time.ctime(), 'magenta', attrs=['underline']) + " "+ colored(msg, color="yellow")
    if len(_log) == 0:
        _log.append(m)
        f=open("log/PyCasterServer.log", 'w')
        f.write(f"LOG STARTED: {time.ctime()}" + '\n' + m)
    else:
        _log.append(m)
        f = open("log/PyCasterServer.log", 'w')
        f.write('\n'.join(_log))

    f.close()
 
def log(msg, evt="info"):
    print(Log(msg, evt))
