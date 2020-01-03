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

# Create your models here.
from django.db import models
from app.models.user import User
from app.models.team import Team 
from datetime import datetime
# Create your models here.
class Judge(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)


class JudgeRequest(models.Model):
    judge = models.ForeignKey(Judge,on_delete=models.CASCADE,related_name="judge_request")
    status = models.CharField(max_length=50,choices=(("approved","Approved"),("rejected","Rejected"),("pending","Pending")),default="pending")
    created_for = models.ForeignKey(User,on_delete=models.CASCADE,related_name="admin_user")
    created_on = models.DateTimeField(auto_now_add=True)
    
class TeamMentorRequest(models.Model): 
    judge_status = models.CharField(max_length=50,choices=(("approved","Approved"),("rejected","Rejected"),("pending","Pending")),default="pending")
    admin_status = models.CharField(max_length=50,choices=(("approved","Approved"),("rejected","Rejected"),("pending","Pending")),default="pending")
    team = models.ForeignKey(Team,on_delete=models.CASCADE,related_name="mentor_request_status")
    for_judge = models.ForeignKey(User,on_delete=models.CASCADE,related_name="for_judge")
    for_admin = models.ForeignKey(User,on_delete=models.CASCADE,related_name="for_admin")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.updated_on = datetime.now()
        return super().save(*args,**kwargs)

class JudgeRequestTeam(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE,related_name="judge_request_team")
    judge = models.ForeignKey(Judge,on_delete=models.CASCADE,related_name="judge_request_team")
    status = models.CharField(max_length=50,choices=(("approved","Approved"),("rejected","Rejected"),("pending","Pending")),default="pending")
    created_for = models.ForeignKey(User,on_delete=models.CASCADE,related_name="admin")
    created_on = models.DateTimeField(auto_now_add=True)
    