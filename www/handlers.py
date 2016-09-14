# -*- coding: utf-8 -*-

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post
from model import User, Check_in, Journal, next_id, Relation
from aiohttp import web
from config import configs
import datetime as dt
import calendar

COOKIE_NAME = 'check_in_session'
_COOKIE_KEY = configs.session.secret
_RE_SHA1 = re.compile(r'^[0-9a-zA-Z]{6,20}$')

def user2cookie(user ,max_age):
    '''
    Generate cookie str by user.
    '''
    # cookie: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    print(s)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '_'.join(L)
    
@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('_')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
        
def wday2weekday(wday):
    '''
    数字转周几
    '''
    wd_dict = {
        0: '周一',
        1: '周二',
        2: '周三',
        3: '周四',
        4: '周五',
        5: '周六',
        6: '周日'
    }
    if not isinstance(wday, int):
        logging.info('wday type error!')
        return None
    if wday not in range(7):
        logging.info('wday value error!')
        return None
    return wd_dict[wday]
    
@asyncio.coroutine
def check_status(year, month, day, name):
    '''
    查询某用户某日是否打卡
    '''
    check_data = yield from Check_in.findAll('user_name=?', [name])
    status = '未打卡'
    if len(check_data) > 0:
        for data in check_data:
            created_date = time.localtime(data.created_at)
            if year == created_date.tm_year and month == created_date.tm_mon and day == created_date.tm_mday:
                status = '已打卡'
                break     
    return status
    
@asyncio.coroutine
def find_journal_data(year, month, day, name):
    '''
    查询某用户某日日志
    '''
    journal_data = yield from Journal.findAll('user_name=?', [name])
    journal = None
    if len(journal_data) > 0:
        for data in journal_data:
            created_date = time.localtime(data.created_at)
            if year == created_date.tm_year and month == created_date.tm_mon and day == created_date.tm_mday:
                journal = data
    return journal
    
def nextLastYearMonth(year, month):
    if month == 1:
        lastYear = year - 1
        lastMonth = 12
        nextYear = year
        nextMonth = 2
    elif month == 12:
        lastYear = year
        lastMonth = 11
        nextYear = year + 1
        nextMonth = 1
    else:
        lastYear = year
        lastMonth = month - 1
        nextYear = year
        nextMonth = month + 1 
    return nextYear, nextMonth, lastYear, lastMonth

    
    
@get('/')
def index(request):
    if request.__user__ is None:
        return web.HTTPFound('/signin')
    user = request.__user__
    name = user.name
    todayTime = time.localtime()
    year = todayTime.tm_year
    month = todayTime.tm_mon
    day = todayTime.tm_mday
    weekday = wday2weekday(todayTime.tm_wday)
    r_dict = {
            '__template__': 'index.html',
            'username': name,
            'year': year,
            'month': month,
            'day': day,
            'weekday': weekday}
    friends = yield from Relation.findAll('active_user_name=?', [name])
    for friend in friends:
        status = yield from check_status(year, month, day, friend.passive_user_name)
        journal = yield from find_journal_data(year, month, day, friend.passive_user_name)
        content = None
        if not type(journal) == type(None):
            content = journal.content   
        friend.status = status
        friend.journal = content
    r_dict['friends'] = friends
    status = yield from check_status(year, month, day, name)
    journal = yield from find_journal_data(year, month, day, name)
    content = None
    if not type(journal) == type(None):
        content = journal.content   
    r_dict['status'] = status
    r_dict['journal'] = content
    return r_dict
    
@get('/about')
def about(request):
    return {
        '__template__': 'about.html'
    }
        
@get('/signup')
def sign_up(request):
    return {
        '__template__': 'signup.html'}
        
@post('/api/signup')
def sign_up_check(*, name, passwd, passwdag):
    # 输入有问题：
    message = ''
    inputError = False
    if not name or not name.strip():
        if len(message) > 0:
            message = message + ';\n请输入用户名'
        else:
            message = message + '请输入用户名'
        inputError = True
    if not passwd or not _RE_SHA1.match(passwd) or not passwdag or not _RE_SHA1.match(passwdag):
        if len(message) > 0:
            message = message + ';\n密码只能由6-20位的字母与数字构成'
        else:
            message = message + '密码只能由6-20位的字母与数字构成'
        inputError = True
    if passwd != passwdag:
        if len(message) > 0:
            message = message + ';\n两次密码不匹配'
        else:
            message = message + '两次密码不匹配'
        inputError = True
    if inputError == True:
        return {
            '__template__': 'signup.html',
            'message': message,
            'username': name}
    # 用户名已被注册
    users = yield from User.findAll('name=?', [name])
    if len(users) > 0:
        message = '用户名已被注册'
        return {
            '__template__': 'signup.html',
            'message': message}
    # 注册用户
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='about:blank')
    yield from user.save()  
    # 分配cookie并转至首页
    r = web.HTTPFound('/')
    cookie = user2cookie(user, 86400)
    r.set_cookie(COOKIE_NAME, cookie, max_age=86400, httponly=True)
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    user.passwd = '******'
    return r
     
@get('/signin')
def sign_in(request):
    return {
        '__template__': 'signin.html'}
        
@post('/api/signin')
def sign_in_check(*, name, passwd):
    if not name:
        return {
            '__template__': 'signin.html',
            'message': '请输入用户名'}
    if not passwd:
        return {
            '__template__': 'signin.html',
            'message': '请输入密码'}
    users = yield from User.findAll('name=?', [name])
    if len(users) == 0:
        return {
            '__template__': 'signin.html',
            'message': '找不到该用户'}
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        return {
            '__template__': 'signin.html',
            'message': '密码错误'}
    r = web.HTTPFound('/')
    cookie = user2cookie(user, 86400)
    r.set_cookie(COOKIE_NAME, cookie, max_age=86400, httponly=True)
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    user.passwd = '******'
    return r

@get('/signout')
def sign_out(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound('/signin')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r
    
@get('/api/check_in')
def check_in_procedure(request):
    user_id = request.__user__.id
    user_name = request.__user__.name
    check_in = Check_in(user_id=user_id, user_name=user_name)
    yield from check_in.save()
    return web.HTTPFound('/')
   
@get('/history')
def find_history(request):
    user = request.__user__
    # 读取年份、月份
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    # 计算每日是周几
    firstDayWDay, monthDays = calendar.monthrange(year, month)
    everyDayData = {}
    for day in range(monthDays):
        wday = (firstDayWDay + day) % 7
        everyDayData[day] = {}
        everyDayData[day]['wday'] = wday2weekday(wday)
        # 调取打卡记录
        everyDayData[day]['status'] = yield from check_status(year, month, day+1, user.name)
        # 调取关注的好友
        friends = yield from Relation.findAll('active_user_name=?', [user.name])
        everyDayData[day]['friends'] = {}
        for friend in friends:
            friend.status = yield from check_status(year, month, day+1, friend.passive_user_name)
            everyDayData[day]['friends']['%s' % friend.passive_user_name] = friend.status
    # 返回
    return {
        '__template__': 'history.html',
        'username': user.name,
        'year': year,
        'month': month,
        'monthDays': monthDays,
        'everyDayData': everyDayData
    }
    
@get('/history/next')    
def find_history_next(request):
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    nextYear, nextMonth, lastYear, lastMonth = nextLastYearMonth(year, month)
    return web.HTTPFound('/history?year=%s&month=%s' % (nextYear, nextMonth))
    
@get('/history/last')    
def find_history_last(request):
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    nextYear, nextMonth, lastYear, lastMonth = nextLastYearMonth(year, month)
    return web.HTTPFound('/history?year=%s&month=%s' % (lastYear, lastMonth))

# 最早写的，配合history_old.html使用 
@get('/history_old')
def find_history_old(*, year, month):
    year = int(year)
    month = int(month)
    firstDay = calendar.monthrange(year, month)[0]
    firstBlock = firstDay - 6 if firstDay == 6 else firstDay + 1   # 将第一天设为周日（datetime模块原来是周一）
    monthDays = calendar.monthrange(year, month)[1]
    r_dict = {
        '__template__': 'history_old.html',
        'year': year,
        'month': month}
    for i in range(firstBlock, firstBlock + monthDays):
        thisDay = i - firstBlock +1
        # 添加日历
        r_dict['block%s' % i] = thisDay
        r_dict['url%s' % i] = '/history/journal?year=%s&month=%s&day=%s' % (year, month, thisDay)
        # 添加feifei打卡情况
        name = 'feifei'
        feifei_status = yield from check_status(year, month, thisDay, name)
        r_dict['feifei%s' % i] = feifei_status
        # 添加maomao打卡情况
        name = 'maomao'
        maomao_status = yield from check_status(year, month, thisDay, name)
        r_dict['maomao%s' % i] = maomao_status        
    return r_dict
    
@get('/history/journal')
def find_history_journal(request):
    # 查询日的信息
    user = request.__user__
    name = user.name
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    day = int(request.GET['day'])
    weekday = wday2weekday(dt.date(year, month, day).weekday())
    r_dict =  {
            '__template__': 'history_journal.html',
            'username': user.name,
            'year': year,
            'month': month,
            'day': day,
            'weekday': weekday,
        }
    # 读取朋友列表、朋友的打卡记录与日志
    friends = yield from Relation.findAll('active_user_name=?', [name])
    for friend in friends:
        status = yield from check_status(year, month, day, friend.passive_user_name)
        journal = yield from find_journal_data(year, month, day, friend.passive_user_name)
        content = None
        if not type(journal) == type(None):
            content = journal.content   
        friend.status = status
        friend.journal = content
    r_dict['friends'] = friends
    # 你至己的打卡信息与日志
    status = yield from check_status(year, month, day, name)
    journal = yield from find_journal_data(year, month, day, name)
    content = None
    if not type(journal) == type(None):
        content = journal.content   
    r_dict['status'] = status
    r_dict['journal'] = content
    return r_dict
    
@get('/write_journal')
def write_journal(request):
    user = request.__user__
    username = user.name
    todayTime = time.localtime()
    year = todayTime.tm_year
    month = todayTime.tm_mon
    day = todayTime.tm_mday
    journal = yield from find_journal_data(year, month, day, user.name)
    content = None
    if not type(journal) == type(None):
        content = journal.content   
    return {
        '__template__': 'write_journal.html',
        'journal': content,
        'username': username}
        
@post('/api/submit_journal')
def submit_journal(request):
    user = request.__user__
    todayTime = time.localtime()
    year = todayTime.tm_year
    month = todayTime.tm_mon
    day = todayTime.tm_mday
    journal = request.POST['journal']
    old_journal = yield from find_journal_data(year, month, day, user.name)
    new_journal = Journal(user_id=user.id, user_name=user.name, content=journal)
    yield from new_journal.save()
    if not type(old_journal) == type(None): 
        yield from old_journal.remove()
    return web.HTTPFound('/')
    
@get('/group')
def group(request):
    user = request.__user__
    name = user.name
    following = yield from Relation.findAll('active_user_name=?', [name])
    noFollowing = False
    if type(following) == type(None):
        noFollowing = True
    follower = yield from Relation.findAll('passive_user_name=?', [name])
    noFollower = False
    if type(follower) == type(None):
        noFollower = True
    return {
        '__template__': 'group.html',
        'username': name,
        'following': following,
        'follower': follower,
        'noFollowing': noFollowing,
        'noFollower': noFollower
    }
    
@post('/api/add_following')
def add_following(request):
    user = request.__user__
    add_following = request.POST['add']
    new_following = yield from User.findAll('name=?', [add_following])
    result = None
    if len(new_following) == 1:
        following_user = new_following[0]
        relations = yield from Relation.findAll('active_user_name=?', [user.name])
        if len(relations) >= 1:
            for relation in relations:
                if relation.passive_user_name == following_user.name:
                    result = 'already following'
            if result != 'already following':
                r1 = Relation(active_user_id=user.id, active_user_name=user.name, passive_user_id=following_user.id, passive_user_name=following_user.name)
                yield from r1.save() 
        else:
            r1 = Relation(active_user_id=user.id, active_user_name=user.name, passive_user_id=following_user.id, passive_user_name=following_user.name)
            yield from r1.save()
    else:
        result = 'User Not Found'
    # 重新载入此页
    following = yield from Relation.findAll('active_user_name=?', [user.name])
    noFollowing = False
    if type(following) == type(None):
        noFollowing = True
    follower = yield from Relation.findAll('passive_user_name=?', [user.name])
    noFollower = False
    if type(follower) == type(None):
        noFollower = True
    return {
        '__template__': 'group.html',
        'username': user.name,
        'following': following,
        'follower': follower,
        'noFollowing': noFollowing,
        'noFollower': noFollower,
        'result': result
    }
    
@get('/api/rm_following')
def rm_following(request):
    user = request.__user__
    following_name = request.GET['following_name']
    relations = yield from Relation.findAll('active_user_name=?', [user.name])
    for relation in relations:
        if relation.passive_user_name == following_name:
            yield from relation.remove()
    return web.HTTPFound('/group')
    
    

    

    
    
