# -*- coding: UTF-8 -*-
"""
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from teste.models import Post


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email', 'groups', 'id')


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = '__all__'
