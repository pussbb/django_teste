# -*- coding: UTF-8 -*-
"""
"""
import concurrent.futures
import os
import random
import re
from pathlib import Path
import string
from configparser import ConfigParser
from functools import wraps
from typing import AnyStr, List, Any

import requests

CONFIG_PATH = (
    os.path.realpath(os.path.dirname(__file__)),
    os.path.join(os.sep, 'etc')
)


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
        request_func = getattr(self._session, method.lower())
        resp = request_func(*args, **kwargs)
        if 200 < resp.status_code > 304:
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
        for post in self.__request(self._build_url('posts')).json():
            yield DictWrapper(post)

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

        result = data['user']
        result['token'] = data['token']
        return DictWrapper({**result, **user_data})

    @auth_require
    def delete_post(self, post_id):
        """

        :param post_id:
        :return: None
        """
        self.__request(self._build_url(f'posts/{post_id}'), method='DELETE')

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

    def like_post(self, post_id: int) -> dict:
        """Like post

        :param post_id:
        :return:
        """
        return self.__post(self._build_url(f'posts/{post_id}/like')).json()

    def dislike_post(self, post_id: int) -> dict:
        """Dislike post

        :param post_id:
        :return:
        """
        return self.__post(self._build_url(f'posts/{post_id}/dislike')).json()


def text_generator(size=8,
                   chars=string.ascii_lowercase + string.digits):
    """Generate random string.

    :param size: length of resulting string
    :param chars: symbols to use
    :return: str
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_config_file(filename: AnyStr) -> AnyStr:
    """Get absolute filename for existing config filename

    :param filename: AnyStr
    :return: absolute file path or none
    """
    for config_path in CONFIG_PATH:
        conf_file = os.path.join(config_path, filename)
        if not os.path.isfile(conf_file):
            continue
        return conf_file


def _add_user(url: AnyStr) -> dict:
    """Creates users in Api server

    :param url: url to Api server
    :return: dict with user details
    """
    bot = BotApiV1(url)
    user = bot.register(
        username=text_generator(),
        password=text_generator(),
        email=f"{text_generator()}@{text_generator()}.com"
    )
    bot.authenticate_token(user.token)
    return user, bot


def _add_posts(user: dict, client: BotApiV1) -> dict:
    """Generate some random articles for user

    :param user: user details
    :param client: BotApiV1 client for user
    :return: dict
    """

    return client.new_post(text_generator(30),
                           text_generator(1024, string.printable))


def _like_posts(user: dict, client: BotApiV1, amount) -> dict:
    """Adds Like or dislike for a post

    :param user:  dict user details
    :param client: BotApiV1 object
    :return: dict
    """
    posts = list(client.posts())
    result = []
    for _ in range(1, amount):
        post = random.choice(posts)
        try:
            res = getattr(
                client,
                random.choice(['like_post', 'dislike_post'])
            )(post.id)
        except ApiException as excp:
            print(excp)
        else:
            res['post'] = post
            result.append(DictWrapper(res))

    return result


def _get_feature_results(features: List) -> dict:
    result = []
    for future in concurrent.futures.as_completed(features):
        try:
            data = future.result()
        except Exception as exc:
            print(f' generated an exception: {exc}')
        else:
            result.append(data)
    return result


def run_bot(url: AnyStr,
            number_of_users: int,
            max_posts_per_user: int,
            max_likes_per_user: int) -> None:
    """

    :param url: AnyStr url of api server
    :param number_of_users: number of users to create
    :param max_posts_per_user: maximum amount of posts that need to create
    :param max_likes_per_user: maximum amount of likes per user
    :return:
    """
    print(url, number_of_users, max_posts_per_user, max_likes_per_user)
    if number_of_users <= 0:
        print('Amount of users not specified exiting')
        return

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=number_of_users) as executor:

        def __run(*args, amount=0):
            return _get_feature_results(
                [executor.submit(*args) for _ in range(0, amount)]
            )
        users = __run(_add_user, url, amount=number_of_users)
        if not users:
            print('Something happened no users were created')
            return

        if max_posts_per_user > 0:
            for user in users:
                user_data, client = user
                amount = random.randint(1, max_posts_per_user)
                posts = __run(_add_posts, *user, amount=amount)
                for indx, post in enumerate(posts, start=1):
                    print(f'Created post #{indx} {post.title} '
                          f'for user {user_data.username}')

        if max_likes_per_user > 0:
            for user in users:
                likes = __run(_like_posts, *user, max_likes_per_user, amount=1)
                for indx, like in enumerate(likes[-1], start=1):
                    action = 'Liked'
                    if like.vote < 0:
                        action = 'Disliked'
                    print(f'{action} post #{indx} {like.post.title} ')


if __name__ == '__main__':
    CONFIG = get_config_file(f'{Path(__file__).stem}.ini')
    if not CONFIG:
        raise SystemExit('Could not find config')

    CONFIG_PARSER = ConfigParser(allow_no_value=True)
    CONFIG_PARSER.read(CONFIG)
    run_bot(
        url=CONFIG_PARSER.get('general', 'api_url'),
        number_of_users=CONFIG_PARSER.getint('general', 'number_of_users'),
        max_posts_per_user=CONFIG_PARSER.getint('general',
                                                'max_posts_per_user'),
        max_likes_per_user=CONFIG_PARSER.getint('general',
                                                'max_likes_per_user'),
    )



"""

bot = BotApiV1('http://127.0.0.1:8000/api/v1')
bot.authenticate('admin', '123456')
print(list(bot.users()))
print(bot.posts())

#print(bot.delete_post(2))
#data = bot.register('as2', 'sdasdasd', '3232242@dsadasddd.com')
#print(data)
#print(bot.authenticate_token(data['token']))

post = bot.new_post(text_generator(), text_generator(1024, string.printable))
print(post)

bot.delete_post(post['id'])

"""
