

from django.contrib import admin
from app.models.organizer import Organizer

class OrganizerAdmin(admin.ModelAdmin):
    fields = ('user', 'title')

admin.site.register(Organizer, OrganizerAdmin)