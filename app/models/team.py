from django.db import models
from app.models.user import User

class Team(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user"
    )
    partipants = models.ManyToManyField('Participant')

    def __unicode__(self):
        return self.name

