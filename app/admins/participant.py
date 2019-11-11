'''
/**
 *@copyright : ToXSL Technologies Pvt. Ltd. < www.toxsl.com >
 *@author     : Shiv Charan Panjeta < shiv@toxsl.com >
 *
 * All Rights Reserved.
 * Proprietary and confidential :  All information contained herein is, and remains
 * the property of ToXSL Technologies Pvt. Ltd. and its partners.
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 *
 *
 */
'''

from django.contrib import admin
from app.models.participant import Participant, TeamRequest

class ParticipantAdmin(admin.ModelAdmin):
    name="he"
    fields = ('user', 'title', 'participant_team')

class TeamRequestAdmin(admin.ModelAdmin):
    fields = ('essay', 'team', 'participant')

admin.site.register(Participant, ParticipantAdmin)
admin.site.register(TeamRequest, TeamRequestAdmin)