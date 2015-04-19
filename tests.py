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
    redis_dict.set_to(py_dict)
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
    def lock_test(cls):
        try:
            with populated_dicts() as (py_dict, redis_dict):
                with redis_dict.acquire_lock(True):
                    with redis_dict.acquire_lock(True):
                        pass
        except RedisLockInUse as exception:
            redis_dict.delete_lock()
        return True

    @classmethod
    def contains_test(cls):
        with populated_dicts() as (py_dict, redis_dict):
            for key in py_dict:
                assert key in redis_dict

@contextmanager
def populated_lists():
    py_list = range(50)
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

    @classmethod
    def slice_test(cls):
        with populated_lists() as (py_list, redis_list):
            assert py_list[1] == redis_list[1]
            assert py_list[-1] == redis_list[-1]
            assert py_list[1:5] == redis_list[1:5]
            assert py_list[1:-2] == redis_list[1:-2]
            assert py_list[1:-2:3] == redis_list[1:-2:3]
            assert py_list[-30:-2:3] == redis_list[-30:-2:3]
            assert py_list[-30:-2:-7] == redis_list[-30:-2:-7]
            assert py_list[-30:30:7] == redis_list[-30:30:7]
            assert py_list[::] == redis_list[::]

    @classmethod
    def del_slice_test(cls):
        with populated_lists() as (py_list, redis_list):
            del(py_list[1])
            del(redis_list[1])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[-1])
            del(redis_list[-1])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[1:5])
            del(redis_list[1:5])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[1:-2])
            del(redis_list[1:-2])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[1:-2:3])
            del(redis_list[1:-2:3])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[-30:-2:3])
            del(redis_list[-30:-2:3])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[-30:-2:-7])
            del(redis_list[-30:-2:-7])
            assert py_list == redis_list
        with populated_lists() as (py_list, redis_list):
            del(py_list[-30:30:7])
            del(redis_list[-30:30:7])
            assert py_list == redis_list
        #with populated_lists() as (py_list, redis_list):
        #    # TODO: figure out what [::] calls on the object
        #    del(py_list[::])
        #    print(py_list)
        #    del(redis_list[::])
        #    print(redis_list)
        #    assert py_list == redis_list

    @classmethod
    def iter_test(cls):
        with populated_lists() as (py_list, redis_list):
            for v1, v2 in izip_longest(py_list, redis_list):
                assert v1 == v2

    @classmethod
    def contains_test(cls):
        with populated_lists() as (py_list, redis_list):
            for value in py_list:
                assert value in redis_list

if __name__ == '__main__':
    RedisDictTests.basic_test()
    RedisDictTests.lock_test()
    RedisDictTests.contains_test()

    RedisListTests.basic_test()
    RedisListTests.slice_test()
    RedisListTests.del_slice_test()
    RedisListTests.iter_test()
    RedisListTests.contains_test()
