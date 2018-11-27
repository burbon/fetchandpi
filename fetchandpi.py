import random
import time

from decimal import Decimal as Dec

import gevent
from gevent import Greenlet
from gevent.pool import Pool
from gevent.event import AsyncResult
from gevent import monkey

import requests


def task(evt, pid, url):
    """
    Some non-deterministic task
    """
    start = time.time()
    requests.get(url)
    print('Task %s done. Took %s' % (pid, time.time() - start))


def pi_approx_classic(evt):
    S, i, sign = 0, 0, 1

    def pi(ppi):
        return 4*ppi

    while True:
        #print('Pi iteration: %s, %s' % (i, pi(S)))
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


def run(pool, evt, url):
    for i in xrange(10):
        pool.start(Greenlet(task, evt, i, url))

    pijob = Greenlet(pi_approx_classic, evt)
    pool.start(pijob)

    while True:
        #print('Pool size: %s' % len(pool))
        if len(pool) == 1 and pijob in pool:
            print('I should die: %s' % evt.get())
            pool.killone(pijob)
            print('and i died: %s' % evt.get())
            return

        gevent.sleep(0)


def main():
    monkey.patch_all()

    evt = AsyncResult()
    pool = Pool()
    url = 'http://slowwly.robertomurray.co.uk/delay/3000/url/https:/www.python.org/'

    start = time.time()
    run(pool, evt, url)
    print('All tasks done. Took %s' % (time.time() - start))

main()
