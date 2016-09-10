# -*- coding: utf-8 -*-

import orm
from model import User, Journal, Check_in, next_id, Relation
import asyncio
import sys
import hashlib

@asyncio.coroutine
def create_users(loop):
    yield from orm.create_pool(loop=loop, user='tonyyeti', password='Tonyalston911', db='check_in_system')
    user_dict = {
        'u1': {
            'name': 'tonyyeti',
            'passwd': 'Tonyalston911',
            'admin': True},
        'u2': {
            'name': 'feifei',
            'passwd': '123456',
            'admin': False},
        'u3': {
            'name': 'maomao',
            'passwd': '123456',
            'admin': False}
            }
    for user in user_dict.values():
        uid = next_id()
        sha1_passwd = '%s:%s' % (uid, user['passwd'])
        u = User(id=uid, name=user['name'], passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='about:blank', admin=user['admin'])
        yield from u.save()
        print(user['name'] + 'saved.')
    feifei = yield from User.findAll('name=?', ['feifei'])
    maomao = yield from User.findAll('name=?', ['maomao'])
    r1 = Relation(active_user_id=feifei[0].id, active_user_name=feifei[0].name, passive_user_id=maomao[0].id, passive_user_name=maomao[0].name)
    r2 = Relation(active_user_id=maomao[0].id, active_user_name=maomao[0].name, passive_user_id=feifei[0].id, passive_user_name=feifei[0].name)
    yield from r1.save()
    print('r1 saved.')
    yield from r2.save()
    print('r2 saved')
    
    
    #check_in = Check_in(user_id=users[0].id, user_name=users[0].name)
    #yield from check_in.save()
    #journal1 = Journal(user_id=users[0].id, user_name=users[0].name, content='123')
    #yield from journal1.save()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_users(loop))
    loop.close()
    if loop.is_closed():
        sys.exit(0)