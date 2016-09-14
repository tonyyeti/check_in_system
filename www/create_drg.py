# -*- coding: utf-8 -*-

import orm
from model import User, Journal, Check_in, next_id, Relation
import asyncio
import sys
import hashlib

@asyncio.coroutine
def create_drg(loop):
    yield from orm.create_pool(loop=loop, user='www-data', password='www-data', db='check_in_system')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, '123')
    drg = User(id=uid, name='drg', passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='about:blank', admin=False )
    yield from drg.save()
    print('drg saved')
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_drg(loop))
    loop.close()
    if loop.is_closed():
        sys.exit(0)
    