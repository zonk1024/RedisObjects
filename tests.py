#!/usr/bin/env python

from __future__ import print_function
from RedisObjects import RedisDict, RedisList, RedisLockInUse
from collections import defaultdict
from contextlib import contextmanager
from itertools import izip_longest
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
    redis_dict.update(py_dict)
    yield (py_dict, redis_dict)
    redis_dict.clear()
    redis_dict.cleanup()

class RedisDictTests(object):

    @classmethod
    def basic_test(cls):
        with populated_dicts() as (py_dict, redis_dict):
            for key in redis_dict:
                assert redis_dict[key] == py_dict[key]
        return True

    @classmethod
    def check_lock(cls):
        try:
            with populated_dicts() as (py_dict, redis_dict):
                with redis_dict.acquire_lock(True):
                    with redis_dict.acquire_lock(True):
                        pass
        except RedisLockInUse as exception:
            redis_dict.delete_lock()
        return True

@contextmanager
def populated_lists():
    py_list = [1, 2, 3, 4]
    redis_list = RedisList('redis_list_test_object')
    redis_list.set_to(py_list)
    yield (py_list, redis_list)
    redis_list.clear()
    redis_list.cleanup()

class RedisListTests(object):
    @classmethod
    def basic_test(cls):
        with populated_lists() as (py_list, redis_list):
            assert py_list == redis_list
            for v1, v2 in izip_longest(py_list, redis_list):
                assert v1 == v2
        return True

if __name__ == '__main__':
    RedisDictTests.basic_test()
    RedisDictTests.check_lock()

    RedisListTests.basic_test()
