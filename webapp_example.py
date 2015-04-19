#!/usr/bin/env python

import flask
from hashlib import sha512
from RedisObjects import RedisDict, RedisList
import redis
import pickle

NAME = 'RedisObjects_example'
app = flask.Flask(NAME)
app.debug = True

####
# Helper classes
####

class UserDoesNotExist(Exception):
    pass

class RedisSession(object):
    def __init__(self, session_id):
        self.session_id = session_id
        self.redis_dict = RedisDict(self.session_key)

    @property
    def session_key(self):
        return 'RedisSession_{}'.format(self.session_id)

    def __dict__(self):
        return self.redis_dict.__dict__()

    def set_dict(self, new_dict):
        self.redis_dict.set_to(new_dict)

    def get(self, key, default=None):
        return self.__dict__().get(key, default)

    def __getitem__(self, key):
        self.redis_dict[key]

    def __setitem__(self, key, value):
        self.redis_dict[key] = value

    def __delitem__(self, key):
        del(self.redis_dict[key])

class User(object):
    userlist = RedisList('{}_userlist'.format(NAME))

    def __init__(self, username):
        self.username = username
        self.redis_dict = RedisDict(self.redis_dict_name(self.username))
        try:
            self.redis_dict['password']
        except KeyError:
            self.redis_dict.clear()
            raise UserDoesNotExist('User "{}" does not exist'.format(username))

    @staticmethod
    def redis_dict_name(username):
        return '{}_user_{}'.format(NAME, username)

    @classmethod
    def login(cls, username, password):
        redis_dict = RedisDict(cls.redis_dict_name(username))
        if redis_dict.get('password', '') == cls.hash_password(password):
            return User(username)

    @classmethod
    def get_user(cls, username):
        try:
            return cls(username)
        except UserDoesNotExist:
            return None

    @classmethod
    def create_user(cls, username, password):
        redis_dict = RedisDict(cls.redis_dict_name(username))
        redis_dict['password'] = cls.hash_password(password)
        if username not in cls.userlist:
            cls.userlist.append(username)
        return cls(username)

    @property
    def password(self):
        return self.redis_dict['password']

    @password.setter
    def password(self, value):
        self.redis_dict['password'] = self.hash_password(value)

    @staticmethod
    def hash_password(password):
        hasher = sha512()
        hasher.update(password)
        return hasher.hexdigest()

    @property
    def email(self):
        return self.redis_dict.get('email', '')

    @email.setter
    def email(self, value):
        self.redis_dict['email'] = value


####
# Endpoints
####

# Index
@app.route('/')
def index():
    session = RedisSession(flask.request.cookies.get('sessionid'))
    username = session.get('username')
    if username is None:
        return flask.redirect('/login')
    try:
        user = User(username)
    except UserDoesNotExist:
        del(session['username'])
        return flask.redirect('/login')
    userlist = '<br />'.join(list(User.userlist))
    return '''<html>
            <body>
                Hello, {}!
                <br />
                <a href="/logout">Logout</a>
                <br />
                <br />
                Users (<a href="/create-user">create</a>):
                <br />
                {}
            </body>
        </html>'''.format(user.username, userlist)

# Login / Logout
@app.route('/login')
def login_get():
    return '''<html>
            <body>
                <form method="POST">
                    <input name="username" value="guest" />
                    <input type="password" name="password" value="guest" />
                    <input type="submit" value="login" />
                </form>
            </body>
        </html>'''

@app.route('/login', methods=['POST'])
def login_post():
    user = User.login(flask.request.form.get('username'), flask.request.form.get('password'))
    if user is None:
        return flask.redirect('/login')
    session = RedisSession(flask.request.cookies.get('sessionid'))
    session['username'] = user.username
    return flask.redirect('/')

@app.route('/logout')
def logout():
    session = RedisSession(flask.request.cookies.get('sessionid'))
    session['username'] = None
    return flask.redirect('/login')

# User creation
@app.route('/create-user')
def create_user_get():
    return '''<html>
            <body>
                <form method="POST">
                    <input name="username" />
                    <input type="password" name="password" />
                    <input type="submit" value="Create User" />
                </form>
            </body>
        </html>'''

@app.route('/create-user', methods=['POST'])
def create_user_post():
    user = User.create_user(flask.request.form.get('username'), flask.request.form.get('password'))
    return flask.redirect('/')


if __name__ == '__main__':
    guest = User.create_user('guest', 'guest')
    app.run('0.0.0.0', 8028)
