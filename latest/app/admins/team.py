

from django.contrib import admin
from app.models.team import Team

class TeamAdmin(admin.ModelAdmin):
    fields = ('name', 'description')

admin.site.register(Team, TeamAdmin)