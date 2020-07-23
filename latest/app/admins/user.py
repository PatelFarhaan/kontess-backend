
from django.contrib import admin
from app.models.user import User

# class TeamAdmin(admin.ModelAdmin):
#     fields = ('name', 'description')

admin.site.register(User)