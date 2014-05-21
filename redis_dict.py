#!/usr/bin/env python

import redis
import pickle


class RedisDict(object):
    # believe it or not, object works better than dict

    def __init__(self, prefix='RedisDict-', host='localhost', port=6379):
        self.prefix = prefix
        self.host = host
        self.port = port
        self.r = self._r()

    def _r(self):
        success = False
        while not success:
            try:
                success = self.r.ping()
            except (redis.ConnectionError, AttributeError):
                self.r = redis.Redis(self.host, self.port)
        return self.r

    def pickle_key(self, key='*'):
        #hash(key)  # throw an error if you must
        return pickle.dumps('{}{}'.format(self.prefix, key))

    def unpickle_key(self, key):
        return pickle.loads(key)[len(self.prefix):]

    def pickle_value(self, value):
        return pickle.dumps(value)

    def unpickle_value(self, value):
        return value if value is None else pickle.loads(value)

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
        return sorted(self.unpickle_key(key)
                      for key in self._r().keys(self.pickle_key()))

    def itervalues(self):
        return (self.__getitem__(key) for key in self.__iter__())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return ((key, self.__getitem__(key)) for key in self.__iter__())

    def items(self):
        return list(self.iteritems())

    def __getitem__(self, key):
        return self.unpickle_value(self._r().get(self.pickle_key(key)))

    def __setitem__(self, key, value):
        if value is None:
            self.__delitem__(key)
            return
        self._r().set(self.pickle_key(key), self.pickle_value(value))

    def __delitem__(self, key):
        self._r().delete(self.pickle_key(key))

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        keys = self.keys()
        for key in keys:
            if keys != self.keys():
                raise RuntimeError("dictionary changed size during iteration")
            yield key

    def __reversed__(self):
        keys = self.keys()
        for key in keys[::-1]:
            if keys != self.keys():
                raise RuntimeError("dictionary changed size during iteration")
            yield key

    def __str__(self):
        return str(self.__dict__())

    def __repr__(self):
        return repr(self.__dict__())

    def __dict__(self):
        return dict(self.items())


if __name__ == '__main__':
    gd = RedisDict()
    gd2 = RedisDict()
    rd = RedisDict()
    print 'init'
    print 'gd', gd
    print 'gd2', gd2
    print 'rd', rd
    print

    del(gd['bob'])
    del(rd['bob'])
    print 'del(dict[\'bob\'])'
    print 'gd', gd
    print 'gd2', gd2
    print 'rd', rd
    print

    print 'It works, but they don\'t seem to show up without a direct call'
    # hence the line 26 comment
    gd[{'x':'Y'}] = {'z': '0'}
    rd[{'x':'Y'}] = {'z': '0'}
    print 'VOODOO!'
    print "gd[{'x':'Y'}] = {'z': '0'}"
    print "rd[{'x':'Y'}] = {'z': '0'}"
    print 'I SEE YOU!'
    print "gd[{'x':'Y'}]", gd[{'x':'Y'}]
    print "rd[{'x':'Y'}]", rd[{'x':'Y'}]
    print 'WTF!?'
    print 'gd', gd
    print 'rd', rd
    print

    gd['bob'] = 'BOB'
    gd[(1, 2)] = {'a':'A', 'b':[1, 2, '3', '4'], 'c':{'d': 'E', 'f': {'g': 'H'}}}
    rd['bob'] = 'BOB'
    rd[(1, 2)] = {'a':'A', 'b':[1, 2, '3', '4'], 'c': {'d': 'E', 'f': {'g': 'H'}}}

    print 'populate'
    print 'gd', gd
    print 'gd2', gd2
    print 'rd', rd
    print

    print 'iterator checks'
    print 'list(gd.iterkeys())', list(gd.iterkeys())
    print 'list(gd.itervalues())', list(gd.itervalues())
    print 'list(gd.iteritems())', list(gd.iteritems())
    print

    print 'get(\'bob\')'
    print 'gd', gd.get('bob')
    print 'gd2', gd2.get('bob')
    print 'rd', rd.get('bob')
    print

    gd.clear()
    rd.clear()
    print 'clear()'
    print 'gd', gd
    print 'gd2', gd2
    print 'rd', rd
    print

    gd['bob'] = 'BOB'
    gd[(1, 2)] = {'a':'A', 'b':[1, 2, '3', '4']}
    rd['bob'] = 'BOB'
    rd[(1, 2)] = {'a':'A', 'b':[1, 2, '3', '4']}
    print 'populate again'
    print 'gd', gd
    print 'gd2', gd2
    print 'rd', rd
    print

    print '\'bob\' in gd', 'bob' in gd
    print '\'bob\' in rd', 'bob' in rd
    print

    print '\'bob3\' in gd', 'bob3' in gd
    print '\'bob3\' in rd', 'bob3' in rd
