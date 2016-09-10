# -*- coding: utf-8 -*-

import time, uuid
from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)
    
class User(Model):
    __table__ = 'users'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)
    
class Journal(Model):
    __table__ = 'journals'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)
    
class Check_in(Model):
    __table__ = 'check_in'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
    checked_in = BooleanField(default=True)
    
class Relation(Model):
    __table__ = 'relations'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    active_user_id = StringField(ddl='varchar(50)')
    active_user_name = StringField(ddl='varchar(50)')
    passive_user_id = StringField(ddl='varchar(50)')
    passive_user_name = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)