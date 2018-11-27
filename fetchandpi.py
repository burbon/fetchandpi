import random
import time

import gevent
from gevent import Greenlet
from gevent.pool import Pool
from gevent.event import AsyncResult


def task(evt, pid):
    """
    Some non-deterministic task
    """
    took = random.randint(0, 5)
    gevent.sleep(took)
    print('Task %s done. Took %s' % (pid, took))


def loop(evt):
    i = 0
    while True:
        i += 1
        evt.set(i)
        print('Pi iteration: %s' % i)

        # making sure gevent yields
        # time.sleep(1)
        gevent.sleep(1)

    return i


def run(pool, evt):
    for i in xrange(10):
        pool.start(Greenlet(task, evt, i))

    pi = Greenlet(loop, evt)
    pool.start(pi)

    while True:
        gevent.sleep(1)
        print('Pool size: %s' % len(pool))
        if len(pool) == 1 and pi in pool:
            print('I should die: %s' % evt.get())
            pool.killone(pi)
            print('and i died: %s' % evt.get())
            return


def main():
    evt = AsyncResult()
    pool = Pool()
    start = time.time()

    run(pool, evt)

    print('All tasks done. Took %s' % (time.time() - start))

main()
