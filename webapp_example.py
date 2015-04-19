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
    def __init__(self, sessionid):
        self.sessionid = sessionid
        self.redis_dict = RedisDict(self.session_key)

    @property
    def session_key(self):
        return 'RedisSession_{}'.format(self.sessionid)

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

    @classmethod
    def get_session(cls):
        sessionid = flask.request.cookies.get('sessionid')
        if sessionid is None:
            return flask.redirect('/login')
        return cls(flask.request.cookies.get('sessionid'))

    @classmethod
    def get_user(cls, redirect=True):
        session = cls.get_session()
        username = session.get('username')
        if username is None:
            if redirect:
                return flask.redirect('/login')
            return
        try:
            user = User(username)
        except UserDoesNotExist:
            del(session['username'])
            if redirect:
                return flask.redirect('/login')
            return
        return User(username)

    @classmethod
    def set_user(cls, user):
        session = cls.get_session()
        if user is None:
            del(session['username'])
            return
        session['username'] = user.username


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

    @classmethod
    def delete_user(cls, username):
        cls.userlist.remove(username)
        user = cls(username)
        user.delete()

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

    def delete(self):
        self.redis_dict.clear()


####
# Endpoints
####

# Index
@app.route('/')
def index():
    user = RedisSession.get_user()
    for username in User.userlist:
        try:
            try_user = User.get_user(username)
        except UserDoesNotExist:
            User.delete_user(username)
    userlist = '<br />'.join('<a href="/edit-user/{}">{}</a> ({}) <a href="/delete-user/{}">delete</a>'.format(username, username, User.get_user(username).email, username) for username in list(User.userlist))
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
    RedisSession.set_user(user)
    return flask.redirect('/')

@app.route('/logout')
def logout():
    RedisSession.set_user(None)
    return flask.redirect('/login')

# User creation
@app.route('/create-user')
def create_user_get():
    user = RedisSession.get_user()
    return '''<html>
            <body>
                <a href="/">home</a>
                <br />
                <br />
                <form method="POST">
                    Username: <input name="username" />
                    <br />
                    Email: <input name="email" />
                    <br />
                    Password: <input type="password" name="password" />
                    <br />
                    <input type="submit" value="Create User" />
                </form>
            </body>
        </html>'''

@app.route('/create-user', methods=['POST'])
def create_user_post():
    user = RedisSession.get_user()
    new_user = User.create_user(flask.request.form.get('username'), flask.request.form.get('password'))
    new_user.email = flask.request.form.get('email', '')
    return flask.redirect('/')

@app.route('/edit-user/<edit_username>')
def edit_user_get(edit_username):
    user = RedisSession.get_user()
    edit_user = User(edit_username)
    return '''<html>
            <body>
                <a href="/">home</a>
                <br />
                <br />
                <form action="/edit-user" method="POST">
                    <input type="hidden" name="username" value="{}" />
                    Username: {} <a href="/delete-user/{}">delete</a>
                    <br />
                    Email: <input name="email" value="{}"/>
                    <br />
                    Password: <input type="password" name="password" />
                    <br />
                    <input type="submit" value="Save User" />
                </form>
            </body>
        </html>'''.format(edit_user.username, edit_user.username, edit_user.username, edit_user.email)

@app.route('/edit-user', methods=['POST'])
def edit_user_post():
    user = RedisSession.get_user()
    edit_username = flask.request.form.get('username')
    edit_user = User.get_user(edit_username)
    if edit_user is None:
        # they shouldn't be here if they didn't even pass a valid username
        RedisSession.set_user(None)
        return flask.redirect('/login')
    password = flask.request.form.get('password')
    if password:
        edit_user.password = password
    email = flask.request.form.get('email')
    if email:
        edit_user.email = email
    return flask.redirect('/')

@app.route('/delete-user/<delete_username>')
def delete_user(delete_username):
    user = RedisSession.get_user()
    try:
        User.delete_user(delete_username)
    except UserDoesNotExist:
        pass
    return flask.redirect('/')


if __name__ == '__main__':
    guest = User.create_user('guest', 'guest')
    app.run('0.0.0.0', 8028)
