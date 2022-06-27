from tornadoweb import *
ConfigLoader.load({})

from core import sched

if __name__ == "__main__":
    sched()

