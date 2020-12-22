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
from django.contrib.auth import get_user_model
import jsonfield


User = get_user_model()

class Events(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True,blank=True)
    location = models.CharField(max_length=255,null=True,blank=True)
    schedule_date = models.CharField(max_length=50)
    attendees = models.CharField(max_length=255,choices=(("participants","participants"),("judges","judges"),("both","both")))
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="events")
    meeting_id = models.CharField(max_length=255,null=True,blank=True)
    join_url = models.CharField(max_length=3000,null=True,blank=True)
    start_url = models.CharField(max_length=3000,null=True,blank=True)

    class Meta:
        ordering=['-created_on','-id']

    def __str__(self):
        return "{}:{}--{}".format(self.schedule_date,self.location,self.title)


class EventLogs(models.Model):
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="log")
    created_for = models.ForeignKey(User,on_delete=models.CASCADE,related_name="elog")
    attendees = models.CharField(max_length=50,choices=(("participant","participant"),("judge","judge")))
    event = models.ForeignKey(Events,on_delete=models.CASCADE,related_name="event_logs")
    is_seen = models.BooleanField(default=True)
