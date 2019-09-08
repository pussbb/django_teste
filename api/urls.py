# -*- coding: UTF-8 -*-
"""
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework_jwt.views import (
    obtain_jwt_token, refresh_jwt_token, verify_jwt_token
)
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'posts', views.PostViewSet)

urlpatterns = [
    path('', include(router.urls)),
    url(r'^auth/refresh', refresh_jwt_token),
    url(r'^auth/verify', verify_jwt_token),
    url(r'^auth/registration/', include('rest_auth.registration.urls')),
    url(r'^auth/', obtain_jwt_token)
]
