from django.contrib import admin
from . import models

# Register your models here.


@admin.register(models.Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'image', 'created','total_likes']
    list_filter = ['created']
    
"""
    def like_count(self, obj):
        return obj.users_like.count()
    like_count.short_description = "Likes"

    def show_likes(self, obj):
        return ", ".join([user.username for user in obj.users_like.all()]) or "-"
    show_likes.short_description = "Users who liked"
    
    """