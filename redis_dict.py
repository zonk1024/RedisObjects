#!/usr/bin/env python

import redis
import pickle


class RedisDict(object):
    # believe it or not, object works better than dict

    def __init__(self, prefix='RedisDict-', host='localhost', port=6379):
        self.prefix = prefix
        self.host = host
        self.port = port

    @property
    def r(self):
        success = False
        while not success:
            try:
                success = self._r.ping()
            except (redis.ConnectionError, AttributeError):
                self._r = redis.Redis(self.host, self.port)
        return self._r

    def pickle_key(self, key='*'):
        hash(key)  # throw an error if you must
        return '{}{}'.format(self.prefix, pickle.dumps(key))

    def unpickle_key(self, key):
        return pickle.loads(key[len(self.prefix):])

    def pickle_value(self, value):
        return pickle.dumps(value)

    def unpickle_value(self, value):
        return None if value is None else pickle.loads(value)

    def len(self):
        return len(self._keys())

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
        return [self.unpickle_key(key) for key in self.r.keys('{}*'.format(self.prefix))]

    def sorted_keys(self):
        return sorted(self._keys())

    def itervalues(self):
        return (self.__getitem__(key) for key in self.__iter__())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return ((key, self.__getitem__(key)) for key in self.__iter__())

    def items(self):
        return list(self.iteritems())

    def __getitem__(self, key):
        return self.unpickle_value(self.r.get(self.pickle_key(key)))

    def __setitem__(self, key, value):
        if value is None:
            self.__delitem__(key)
            return
        self.r.set(self.pickle_key(key), self.pickle_value(value))

    def __delitem__(self, key):
        self.r.delete(self.pickle_key(key))

    def __contains__(self, key):
        return key in self.keys()

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


if __name__ == '__main__':
    # dictionary check
    d = {}
    rd = RedisDict()
    rd.clear()

    d['foo'] = 5
    rd['foo'] = 5

    d['bar'] = [1, 2, 3]
    rd['bar'] = [1, 2, 3]

    d['baz'] = {}
    rd['baz'] = {}

    d[(0, 1)] = {'1': 1, '2': 2}
    rd[(0, 1)] = {'1': 1, '2': 2}

    assert set(d.keys()) == set(rd.keys())

    for k in rd:
        assert d[k] == rd[k]

    assert d == rd

    rd.clear()
    rd.update(d.items())

    assert d == rd

    rd.clear()
