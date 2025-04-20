from django.contrib import admin

from network.models import Like, Posts, User

# Register your models here.
admin.site.register(User)
admin.site.register(Posts)
admin.site.register(Like)
