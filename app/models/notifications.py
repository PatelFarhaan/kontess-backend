from django.db import models
from django.contrib.auth import get_user_model
import jsonfield
from bson.json_util import default


User = get_user_model()

class Notification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")
    created_for = models.ForeignKey(User,on_delete=models.CASCADE,related_name="_notification")
    type = models.CharField(max_length=255,choices=(("request","request"),("response","response")))
    req_data = jsonfield.JSONField(default={})
    is_seen = models.BooleanField(default=True)
    
    class Meta:
        ordering=['-created_on','-id']
    
    def __str__(self):
        return self.title