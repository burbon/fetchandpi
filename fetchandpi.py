import random
import time

from decimal import Decimal as Dec

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


def pi_approx_classic(evt):
    S, i, sign = 0, 0, 1

    def pi(ppi):
        return 4*ppi

    while True:
        print('Pi iteration: %s, %s' % (i, pi(S)))
        S += Dec(float(sign) / (2*i+1))
        evt.set(pi(S))

        i += 1
        sign = -sign

        # making sure gevent yields
        gevent.sleep(0)


def pi_approx_ng(evt):
    K, M, L, X, S, i = 6, 1, 13591409, 1, 13591409, 1

    def pi(ppi):
        return 426880 * Dec(10005).sqrt() / ppi

    while True:
        print('Pi iteration: %s, %s' % (i, pi(S)))
        M = (K**3 - 16*K) * M // i**3
        L += 545140134
        X *= -262537412640768000

        S += Dec(M * L) / X
        evt.set(pi(S))

        K += 12
        i += 1

        # making sure gevent yields
        gevent.sleep(0)


def run(pool, evt):
    for i in xrange(10):
        pool.start(Greenlet(task, evt, i))

    pi = Greenlet(pi_approx_classic, evt)
    pool.start(pi)

    while True:
        print('Pool size: %s' % len(pool))
        if len(pool) == 1 and pi in pool:
            print('I should die: %s' % evt.get())
            pool.killone(pi)
            print('and i died: %s' % evt.get())
            return

        gevent.sleep(0)


def main():
    evt = AsyncResult()
    pool = Pool()
    start = time.time()

    run(pool, evt)

    print('All tasks done. Took %s' % (time.time() - start))

main()
