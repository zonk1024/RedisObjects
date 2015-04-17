#!/usr/bin/env python

from itertools import izip
from contextlib import contextmanager
import redis
import pickle
import atexit


class RedisConnectionManager(object):
    cons = {}

    @classmethod
    def r(cls, obj):
        success = False
        while not success:
            try:
                success = cls.cons[(obj.host, obj.port)].ping()
            except (redis.ConnectionError, KeyError):
                cls.cons[(obj.host, obj.port)] = redis.Redis(obj.host, obj.port)
        return cls.cons[(obj.host, obj.port)]


class RedisObject(object):
    instances = []

    def __init__(self, name='RedisObject-', host='localhost', port=6379):
        self.name = name
        self.host = host
        self.port = port
        self.instances.append(self)

    @property
    def r(self):
        return RedisConnectionManager.r(self)

    @property
    def lock_name(self):
        return '{}LOCK'.format(self.name)

    def __del__(self):
        self.r.delete(self.name)

    def delete_lock(self):
        while self.r.incr(self.lock_name) != 1:
            self.r.decr(self.lock_name)
        self.r.delete(self.lock_name)

    @contextmanager
    def acquire_lock(self):
        while self.r.incr(self.lock_name) != 1:
            self.r.decr(self.lock_name)
        yield
        self.r.decr(self.lock_name)

    @classmethod
    def cleanup(cls):
        for instance in cls.instances:
            instance.delete_lock()

    def pickle(self, value):
        return pickle.dumps(value)

    def unpickle(self, value):
        return None if value is None else pickle.loads(value)


class RedisDict(RedisObject):
    def len(self):
        return len(self.keys())

    def clear(self):
        for key in self.keys():
            self.__delitem__(key)

    def pop(self, key, default=None):
        value = self.__getitem__(key)
        self.__delitem__(key)
        return value or default

    def popitem(self):
        key = self.keys()[0]
        value = self.__getitem__(key)
        self.__delitem__(key)
        return key, value

    def setdefault(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return value
        self.__setitem__(key, default)
        return default

    def get(self, key, default=None):
        return self.__getitem__(key) or default

    def update(self, iterable, **kwargs):
        if type(iterable) in (dict, RedisDict):
            self.update(iterable.items(), **kwargs)
        iterable.extend(kwargs.items())
        for key, value in iterable:
            self.__setitem__(key, value)

    def iterkeys(self):
        return self.__iter__()

    def keys(self):
        return [self.unpickle(key) for key in self.r.hkeys(self.name)]

    def sorted_keys(self):
        return sorted(self.keys())

    def itervalues(self):
        return (value for key, value in self.iteritems())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return ((self.unpickle(key), self.unpickle(value)) for key, value in self.r.hgetall(self.name))

    def items(self):
        return list(self.iteritems())

    def __getitem__(self, key):
        return self.unpickle(self.r.hget(self.name, self.pickle(key)))

    def __setitem__(self, key, value):
        if value is None:
            self.__delitem__(key)
            return
        self.r.hset(self.name, self.pickle(key), self.pickle(value))

    def __delitem__(self, key):
        self.r.hdel(self.name, self.pickle(key))

    def __contains__(self, key):
        return self.hexists(self.name, self.pickle(key))

    def __iter__(self):
        keys = self.keys()
        for key in keys:
            if keys != self.keys():
                raise RuntimeError("RedisDict changed size during iteration")
            yield key

    def __reversed__(self):
        keys = self.keys()
        for key in keys[::-1]:
            if keys != self.keys():
                raise RuntimeError("RedisDict changed size during iteration")
            yield key

    def __str__(self):
        return str(self.__dict__())

    def __repr__(self):
        return repr(self.__dict__())

    def __dict__(self):
        return dict(self.items())

    def __eq__(self, other):
        if type(other) not in (dict, RedisDict):
            return False
        for k in self:
            if other[k] != self[k]:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return self.len()


class RedisList(RedisObject):
    def append(self, value):
        self.r.rpush(self.name, self.pickle(value))

    def extend(self, values):
        self.r.rpush(self.name, *[self.pickle(value) for value in values])

    def insert(self, index, value):
        self.r.linsert(self.name, index, self.pickle(value))

    def remove(self, value):
        self.r.lrem(self.name, value)

    def pop(self, index=-1):
        length = len(self)
        if index < 0:
            if index + length < 0:
                raise IndexError('RedisList index out of range')
            return self.unpickle(self.r.lrem(self.name, length + index))
        if index > length - 1:
            raise IndexError('RedisList index out of range')
        return self.unpickle(self.r.lrem(self.name, index))

    def index(self, value):
        index = self.r.index(self.name, self.pickle(value))
        if index is None:
            raise ValueError('{} is not in RedisList'.format(repr(value)))
        return index

    def count(self, value):
        count = 0
        for v in self.__list__():
            if v == value:
                count += 1
        return count

    def sort(self, *args, **kwargs):
        temp = sorted(self.__list__(), *args, **kwargs)
        self.r.delete(self.name)
        self.r.rpush(self.name, *temp)
        return temp

    def reverse(self):
        temp = self.__list__()[::-1]
        self.r.delete(self.name)
        self.r.rpush(self.name, *[self.pickle(t) for t in temp])

    def clear(self):
        self.r.delete(self.name)

    def __add__(self, value):
        if type(value) is list:
            return self.__list__() + value
        if type(value) is RedisList:
            return self.__list__() + value.__list__()
        raise TypeError('can only concatenate list or RedisList (not "{}") to RedisList'.format(type(value)))

    def __delitem__(self, index):
        self.pop(index)

    def __delslice__(self, i, j, n=1):
        temp = self.__list__()
        del(temp[i:j:n])
        self.r.delete(self.name)
        self.r.rpush(self.name, *[self.pickle(t) for t in temp])

    def __list__(self):
        return [self.unpickle(value) for value in self.r.lrange(self.name, 0, -1)]

    def __str__(self):
        return str(self.__list__())

    def __repr__(self):
        return repr(self.__list__())

    def __eq__(self, other):
        if type(other) in (list, RedisList):
            return all(a == b for a, b in izip(self.__list__(), other))
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __contains__(self, value):
        try:
            self.index(value)
            return True
        except ValueError:
            return False

    def __iter__(self):
        length = len(self)
        i = 0
        while i < length - 1:
            if length != len(self):
                raise RuntimeError("RedisList changed size during iteration")
            yield self.r.index(self.name, i)
            i += 1

    def __len__(self):
        return self.r.llen(self.name)


class RedisSet(RedisObject):
    pass


class RedisSortedSet(RedisObject):
    pass


atexit.register(RedisObject.cleanup)

if __name__ == '__main__':
    ##################
    # dictionary check
    d = {}
    rd = RedisDict('RedisDict_test')
    rd.clear()

    d['foo'] = 5
    with rd.acquire_lock():
        rd['foo'] = 5

    d['bar'] = [1, 2, 3]
    with rd.acquire_lock():
        rd['bar'] = [1, 2, 3]

    d['baz'] = {}
    with rd.acquire_lock():
        rd['baz'] = {}

    d[(0, 1)] = {'1': 1, '2': 2}
    with rd.acquire_lock():
        rd[(0, 1)] = {'1': 1, '2': 2}

    assert set(d.keys()) == set(rd.keys())

    for k in rd:
        assert d[k] == rd[k]

    assert d == rd

    rd.clear()

    with rd.acquire_lock():
        rd.update(d.items())

    assert d == rd

    rd.clear()


    ############
    # list check
    l = []
    rl = RedisList('RedisList_test')

    l.append(5)
    rl.append(5)

    l.append('bob')
    with rl.acquire_lock():
        rl.append('bob')

    assert l == rl

    rl.clear()
