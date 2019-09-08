# -*- coding: UTF-8 -*-
"""
"""
import random
import re
import string
from functools import wraps
from typing import AnyStr, List, Any

import requests


def reduce_slashes(url: AnyStr) -> AnyStr:
    """Reduce slashes in url

    :param url:
    :return: string
    """
    return re.sub(r'(?<!:)\/\/+', '/', url)


class DictWrapper(dict):
    """Helper wrapper for a dict with a few helper things
    """

    def __getattr__(self, item):
        return self[item]


class ApiException(Exception):
    """Helper Exception class to get errors from API response

    """

    def __init__(self, message: AnyStr, response: requests.Response):
        super().__init__(message)
        self._resp = response
        self._errors = {}
        try:
            self._errors = response.json()
        except ValueError as _:
            pass

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        self.__str__().encode()

    def __str__(self):
        return f'{self._errors}'

    @property
    def errors(self) -> dict:
        """Errors return by api server

        :return: dict
        """
        return self._errors


def auth_require(func: callable) -> Any:
    """Simple wrapper to prevent unauthorized http requests to API server

    :param func: callable
    :return: Any
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._session.headers.get('Authorization', None):
            raise ApiException('Please authorize first', requests.Response())
        return func(self, *args, **kwargs)
    return wrapper


class BotApiV1:
    """Simple Api client

    """

    def __init__(self, host):
        self.__host = host
        self._session = requests.Session()
        self._session.verify = False  # ignore self signed certificates
        self._session.headers['Accept'] = 'application/json'
        self._me = {}

    def _build_url(self, uri: AnyStr) -> AnyStr:
        """builds full url to api .

        :param uri: Anystr
        :return:
        """
        return reduce_slashes(f'{self.__host}/{uri}/')

    def __post(self, *args, **kwargs) -> requests.Response:
        """Helper method to make a POST http request

        :param args:
        :param kwargs:
        :return: requests.Response
        """
        return self.__request(*args, **kwargs, method='POST')

    def __request(self, *args, method='GET', **kwargs) -> requests.Response:
        """Makes HTTP requests with HTTP status checks

        :param args:
        :param method:
        :param kwargs:
        :return: requests.Response
        """
        request_func = self._session.get
        if method.lower() != 'get':
            request_func = self._session.post

        resp = request_func(*args, **kwargs)
        if resp.status_code not in [200, 201, 301, 302, 304]:
            raise ApiException(
                'Api request failed. {}'.format(resp.status_code),
                resp
            )
        return resp

    def authenticate_token(self, token) -> None:
        """

        :param token:
        :return:
        """
        try:
            self.__post(self._build_url('auth/verify'), {'token': token})
        except ApiException as _:
            del self._session.headers['Authorization']
            raise
        else:
            self._session.headers['Authorization'] = f'JWT {token}'

    def authenticate(self, username: AnyStr, password: AnyStr) -> None:
        """Authenticate user

        :param username:  username or email
        :param password: string ema
        :return: None
        """
        auth_data = {
            'username': username,
            'password': password
        }
        resp = self.__post(self._build_url('auth'), data=auth_data)
        self._session.headers['Authorization'] = f'JWT {resp.json()["token"]}'

    @property
    @auth_require
    def me(self):
        if not self._me:
            self._me = DictWrapper(
                self.__request(self._build_url('users/me')).json()
            )
        return self._me

    @auth_require
    def users(self) -> List:
        """Get user list from api

        :return: list of dict with user attributes
        """
        for user in self.__request(self._build_url('users')).json():
            yield DictWrapper(user)

    @auth_require
    def posts(self) -> List:
        """Get posts .

        :return: list of posts
        """
        return self.__request(self._build_url('posts')).json()

    @auth_require
    def register(self, username, password, email) -> dict:
        """Register new user with provided data

        :param username: string desired user name
        :param password: string user password
        :param email: string user email
        :return:
        """
        user_data = {
            'username': username,
            'password1': password,
            'password2': password,
            'email': email
        }

        data = self.__post(
            self._build_url('auth/registration'),
            user_data
        ).json()
        result = DictWrapper(data['user'])
        result['token'] = data['token']
        return result

    @auth_require
    def new_post(self, title: AnyStr, body: AnyStr) -> dict:
        """Create new post item

        :param title: string
        :param body: string
        :return: dict with new post details
        """
        data = self.__post(
            self._build_url('posts'),
            {
                'title': title,
                'content': body,
                'author': self.me.id
            }
        ).json()

        return DictWrapper(data)


def text_generator(size=8,
                   chars=string.ascii_lowercase + string.digits):
    """Generate random string.

    :param size: length of resulting string
    :param chars: symbols to use
    :return: str
    """
    return ''.join(random.choice(chars) for _ in range(size))


bot = BotApiV1('http://127.0.0.1:8000/api/v1')
bot.authenticate('admin', '123456')
print(list(bot.users()))
print(bot.posts())
#data = bot.register('sddddaasddas', 'sdasdasd', 'ssd23sd@dsadasddd.com')
#print(bot.authenticate_token(data['token']))

print(bot.new_post(text_generator(), text_generator(1024, string.printable)))