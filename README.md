redis_dict
==========

Simple to use:
rd = RedisDict()
rd['key'] = value
rd.items()
[('key', 'value')]

Need to clear the values?
rd.clear()

Different host?
rd = RedisDict(host='notlocalhost')

Different namespace?
rd = RedisDict('different-namespace')

THANKS!
-------
Thanks to Andy Schmitt and Parthenon Software Group
for letting me post this to github.
