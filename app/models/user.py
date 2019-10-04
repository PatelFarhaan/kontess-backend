from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_judge = models.BooleanField('judge status', default=False)
    is_participant = models.BooleanField('participant status', default=False)
    is_organizer = models.BooleanField('organizer status', default=False)