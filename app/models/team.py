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
from enum import unique

class Team(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    logo = models.FileField(upload_to="team")
    team_mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentor",
        verbose_name="team mentor",
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user"
    )
    team_lead= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user",
        related_name="team_lead",
        null=True,blank=True,
    )
    partipants = models.ManyToManyField('Participant',related_name="team_members")
    created_on = models.DateTimeField(auto_now_add=True)
    team_track= models.ForeignKey('TeamTrack',on_delete=models.CASCADE,related_name="teams",null=True,blank=True)
    
    def __unicode__(self):
        return self.name
    
#     class Meta:
#         ordering=["-id"]


class TeamPortfolio(models.Model):
    docs = models.FileField(upload_to="team")
    team =  models.ForeignKey(Team,on_delete=models.CASCADE,related_name="portfolio")


class TeamTrack(models.Model):
    track_name= models.CharField(max_length=255)
    slug = models.CharField(max_length=255,unique=True)
    description = models.TextField(null=True,blank=True)
    
    def save(self,*args,**kwargs):
        if self.track_name:
            self.slug= "_".join(self.track_name.lower().split(" "))
            
        return super().save(*args,**kwargs)
        
    
class Invitation(models.Model):
    participants = models.ForeignKey('Participant',on_delete=models.CASCADE,related_name="invites")
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="team")
    status = models.CharField(max_length=50,choices=(("pending","pending"),("rejected","rejected"),("accepted","accepted")))
    created_on= models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="user",related_name="team_invitations")
    email_send= models.BooleanField(default=False)
    