from tornadoweb import *
ConfigLoader.load({})

from core import sched_start

if __name__ == "__main__":
    sched_start()

