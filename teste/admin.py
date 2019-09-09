from django.contrib import admin

from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'likes', 'dislikes')


admin.site.register(Post, PostAdmin)
