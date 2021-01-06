

from django.db import models
from django.contrib.auth import get_user_model
import jsonfield


User = get_user_model()

class Notification(models.Model):
    TYPE=(
        ("request","request"),
        ("response","response"),
        ("invitation","invitation"),
        ("judge-request","judge-request"),
        ("mentor-request","mentor-request"),
        ("mentor-status","mentor-status"),
        ("judge-request-team","judge-request-team")
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")
    created_for = models.ForeignKey(User,on_delete=models.CASCADE,related_name="_notification")
    type = models.CharField(max_length=255,choices=TYPE)
    req_data = jsonfield.JSONField(default={})
    is_seen = models.BooleanField(default=True)


    def __str__(self):
        return self.title


