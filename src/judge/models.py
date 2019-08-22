from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Judge(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=20)

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)
