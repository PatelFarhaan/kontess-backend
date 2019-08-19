from django.contrib import admin
from .models import Team

class TeamAdmin(admin.ModelAdmin):
    fields = ('name', 'description')

admin.site.register(Team, TeamAdmin)