from django.contrib import admin
from .models import Participant, TeamRequest

class ParticipantAdmin(admin.ModelAdmin):
    name="he"
    fields = ('user', 'graduation_year', 'team')

class TeamRequestAdmin(admin.ModelAdmin):
    fields = ('essay', 'team', 'participant')

admin.site.register(Participant, ParticipantAdmin)
admin.site.register(TeamRequest, TeamRequestAdmin)