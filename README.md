RedisObjects
============

Simple to use:

rd = RedisDict('myredisdict')

rd['key'] = 'value'

rd.items()

[('key', 'value')]


Need to clear the values?

rd.clear()


Different host and port?

rd = RedisDict('myredisdict', host='notlocalhost', port=6380)


THANKS!
-------
Thanks to Andy Schmitt and Parthenon Software Group for letting me post this to github.
