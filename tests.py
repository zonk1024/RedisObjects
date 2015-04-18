#!/usr/bin/env python

from __future__ import print_function
from RedisObjects import RedisDict, RedisList, RedisLockInUse
from collections import defaultdict
from contextlib import contextmanager
from sets import ImmutableSet
tests = defaultdict(list)

##################
# RedisDict check

@contextmanager
def populated_dicts():
    py_dict = {
        1: [1],
        '1': ['1'],
        (1, ): [(1, )],
        ('1', ): [('1', )],
        2: {},
        '2': {2: {}},
        ImmutableSet((3, )): set((3, )),
    }
    redis_dict = RedisDict('redis_dict_test_object')
    redis_dict.clear()
    redis_dict.delete_lock()
    with redis_dict.acquire_lock(raise_exception=True):
        redis_dict.update(py_dict.items())
    yield (py_dict, redis_dict)
    redis_dict.clear()
    redis_dict.cleanup()

class RedisDictTests:
    @classmethod
    def basic_test(cls):
        with populated_dicts() as (py_dict, redis_dict):
            print(py_dict)
            print(redis_dict)
            for key in redis_dict:
                assert redis_dict[key] == py_dict[key]

    @classmethod
    def check_lock(cls):
        with populated_dicts() as (py_dict, redis_dict):
            with redis_dict.acquire_lock(True):
                try:
                    with redis_dict.acquire_lock(True):
                        print('This shouldn\'t happen')
                except RedisLockInUse as exception:
                    redis_dict.delete_lock()
                    redis_dict.clear()
                    print(exception)


def list_check():
    ############
    # list check
    l = []
    rl = RedisList('RedisList_test')

    l.append(5)
    rl.append(5)

    l.append('bob')
    with rl.acquire_lock(True):
        rl.append('bob')

    assert l == rl

    rl.clear()

if __name__ == '__main__':
    RedisDictTests.basic_test()
    RedisDictTests.check_lock()
    list_check()
