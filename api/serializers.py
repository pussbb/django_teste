# -*- coding: UTF-8 -*-
"""
"""
from datetime import datetime

from rest_framework import serializers
from django.contrib.auth.models import User

from teste.models import Post, Vote


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email', 'groups', 'id')


class VoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vote
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.title = validated_data.get('title', instance.title)
        instance.updated_on = validated_data.get('updated_on', datetime.now())
        return instance
