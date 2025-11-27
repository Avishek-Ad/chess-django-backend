from django.contrib import admin

from .models import User
admin.site.register(User)

# not currently using
# admin.site.register(UserProfile)
# admin.site.register(FriendRequest)