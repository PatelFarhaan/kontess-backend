
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
    meeting_id = models.CharField(max_length=255, null=True, blank=True, default="")
    join_url = models.CharField(max_length=3000, null=True, blank=True, default="")
    start_url = models.CharField(max_length=3000, null=True, blank=True, default="")

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
