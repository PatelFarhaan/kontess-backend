from django.db import models
from app.models.user import User

# Create your models here.
class Organizer(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)
