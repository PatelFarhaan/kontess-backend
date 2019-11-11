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

from django.db import models
from app.models.user import User
from app.models.team import Team

# Create your models here.
class Participant(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )
    participant_team = models.ForeignKey("app.Team",
        verbose_name=("participants team"), 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team_members"
    )

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)

class TeamRequest(models.Model):
    essay = models.CharField(("request reason"), max_length=500)
    team = models.ForeignKey(
        Team, 
        verbose_name=("the team that's being requested"), 
        on_delete=models.CASCADE,
        related_name="team_request",
    )
    participant = models.ForeignKey(
        Participant, 
        verbose_name=("participant"), 
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=20,choices=(("pending","pending"),("rejected","rejected"),("approved","approved")),null=True,blank=True)
    
    def __unicode__(self):
        return "{0} - #{1} {2} {3}".format(
            self.team.name, 
            self.participant.id,
            self.participant.user.first_name, 
            self.participant.user.last_name
        )