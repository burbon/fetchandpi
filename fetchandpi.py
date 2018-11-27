#!/usr/bin/env python
from decimal import Decimal, getcontext
import hashlib
import random
import time

import gevent
from gevent import Greenlet
from gevent.pool import Pool
from gevent.event import AsyncResult
from gevent import monkey

monkey.patch_all()

import requests
import click


def dld(evt, pid, url):
    """
    Downloads url content into memory
    """
    start = time.time()
    resp = requests.get(url)
    stats = {
        'pid': pid,
        'duration': "%.3f" % (time.time() - start),
        'size': len(resp.content),
        'checksum': hashlib.sha256(resp.content).hexdigest()
    }

    return stats


def pi_approx_classic(evt):
    """
    Classical approach to pi approximation - Madhava-Leibniz.
    It converges too slowly to be of practical interest.
    """
    S, i, sign = 0, 0, 1

    def pi(ppi):
        return 4*ppi

    while True:
        #print('Pi iteration: %s, %s' % (i, pi(S)))
        S += Decimal(sign) / (2*i+1)
        evt.set({'pi': pi(S), 'i': i})

        i += 1
        sign = -sign

        # making sure gevent yields
        gevent.sleep(0)


def pi_approx_ng(evt):
    """
    https://en.wikipedia.org/wiki/Chudnovsky_algorithm
    was used in the world record calculations of 2.7 trillion digits of pi in December 2009
    """
    K, M, L, X, S, i = 6, 1, 13591409, 1, 13591409, 1

    def pi(ppi):
        return 426880 * Decimal(10005).sqrt() / ppi

    while True:
        #print('Pi iteration: %s, %s' % (i, pi(S)))
        M = (K**3 - 16*K) * M // i**3
        L += 545140134
        X *= -262537412640768000

        S += Decimal(M * L) / X
        evt.set({'pi': pi(S), 'i': i})

        K += 12
        i += 1

        # making sure gevent yields
        gevent.sleep(0)


def run(pool, evt, url, pi_approx):
    dldjobs = []
    for i in xrange(10):
        dldjob = Greenlet(dld, evt, i, url)
        pool.start(dldjob)
        dldjobs.append(dldjob)

    pijob = Greenlet(pi_approx, evt)
    pool.start(pijob)

    while True:
        #print('Pool size: %s' % len(pool))
        if len(pool) == 1 and pijob in pool:
            pool.killone(pijob)
            print('JOB pi: %s' % evt.get())

            for dldjob in dldjobs:
                print('JOB dld: %s' % dldjob.value)

            return

        gevent.sleep(0)


@click.command()
@click.option('--quality/--no-quality', default=False, help='Quality Pi')
def main(quality):
    if not quality:
        pi_approx = pi_approx_classic
    else:
        pi_approx = pi_approx_ng
        getcontext().prec = 200

    evt = AsyncResult()
    pool = Pool()
    url = 'http://slowwly.robertomurray.co.uk/delay/3000/url/https:/www.python.org/'
    url = 'https://www.python.org/'

    start = time.time()
    run(pool, evt, url, pi_approx)
    print('All tasks done. Took %s' % (time.time() - start))

main()
