#!/usr/bin/env python
from decimal import Decimal, getcontext
import hashlib
import logging
import time

import gevent
from gevent import Greenlet
from gevent.pool import Pool
from gevent.event import AsyncResult
from gevent import monkey

monkey.patch_all()

import requests
import click


def dld(pid, config):
    """
    Downloads url content into memory
    """
    logging.debug('started downloading: %s', pid)
    start = time.time()
    resp = requests.get(config['url'])

    if config['delay']:
        time.sleep(config['delay'])

    stats = {
        'pid': pid,
        'duration': "%.3f" % (time.time() - start),
        'size': len(resp.content),
        'checksum': hashlib.sha256(resp.content).hexdigest()
    }

    logging.debug('finished downloading: %s', pid)

    return stats


def pi_approx_classic(evt, config):
    """
    Classical approach to pi approximation - Madhava-Leibniz.
    It converges too slowly to be of practical interest.
    """
    S, i, sign = 0, 0, 1

    def pi(ppi):
        return 4*ppi

    while True:
        logging.debug('Pi iteration: %s, %s', i, pi(S))
        S += Decimal(sign) / (2*i+1)
        evt.set({'pi': pi(S), 'i': i})

        i += 1
        sign = -sign

        # making sure greenlet yields
        if i % config['piswitch'] == 0:
            gevent.sleep(0)


def pi_approx_ng(evt, config):
    """
    https://en.wikipedia.org/wiki/Chudnovsky_algorithm
    was used in the world record calculations of 2.7 trillion digits of pi
    in December 2009
    """
    K, M, L, X, S, i = 6, 1, 13591409, 1, 13591409, 1

    def pi(ppi):
        return 426880 * Decimal(10005).sqrt() / ppi

    while True:
        logging.debug('Pi iteration: %s, %s', i, pi(S))
        M = (K**3 - 16*K) * M // i**3
        L += 545140134
        X *= -262537412640768000

        S += Decimal(M * L) / X
        evt.set({'pi': pi(S), 'i': i})

        K += 12
        i += 1

        # making sure greenlet yields
        if i % config['piswitch'] == 0:
            gevent.sleep(0)


def run(run_config, dld_config, pi_config):
    evt = AsyncResult()
    pool = Pool(run_config['greenlets'])

    dldjobs = []
    for i in xrange(run_config['copies']):
        dldjob = Greenlet(dld, i, dld_config)
        pool.start(dldjob)
        dldjobs.append(dldjob)

    pi_approx = pi_config.pop('pi_approx')
    pijob = Greenlet(pi_approx, evt, pi_config)
    pool.start(pijob)

    while True:
        logging.debug('Pool size: %s' % len(pool))
        if len(pool) == 1 and pijob in pool:
            pool.killone(pijob)
            print('JOB pi: %s' % evt.get())

            for dldjob in dldjobs:
                print('JOB dld: %s' % dldjob.value)

            return

        gevent.sleep(0)


@click.command()
@click.option('--quality/--no-quality', default=False, help='Quality Pi')
@click.option('--copies', default=10, help='Download copies')
@click.option('--greenlets', default=11, help='Download greenlets')
@click.option('--debug/--no-debug', default=False, help='Debug')
@click.option('--delay', default=3, help='Download delay')
@click.option('--piswitch', default=1, help='Pi approx iter context switch')
def main(quality, copies, greenlets, debug, delay, piswitch):
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    pi_approx = pi_approx_classic
    if quality:
        pi_approx = pi_approx_ng
        getcontext().prec = 200

    url = 'http://slowwly.robertomurray.co.uk/delay/3000/url/https:/www.python.org/'
    if delay:
        url = 'https://www.python.org/'

    dld_config = {
        'url': url,
        'delay': delay,
    }
    pi_config = {
        'pi_approx': pi_approx,
        'piswitch': piswitch,
    }
    run_config = {
        'copies': copies,
        'greenlets': greenlets,
    }

    start = time.time()
    run(run_config, dld_config, pi_config)
    print('All tasks done. Took %s' % (time.time() - start))

main()
