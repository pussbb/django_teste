# -*- coding: UTF-8 -*-
"""
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):

    message = 'You must be the creator of this object.'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user