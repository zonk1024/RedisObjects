#!/usr/bin/env python
"""
This is BS.  It's not full on tests yet.
"""

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
