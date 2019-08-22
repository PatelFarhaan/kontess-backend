from django.contrib import admin
from .models import Organizer

class OrganizerAdmin(admin.ModelAdmin):
    fields = ('user', 'title')

admin.site.register(Organizer, OrganizerAdmin)