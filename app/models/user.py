from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    full_name = models.CharField(max_length=100, default="")

    is_judge = models.BooleanField('judge status', default=False)
    is_participant = models.BooleanField('participant status', default=False)
    is_organizer = models.BooleanField('organizer status', default=False)

    @property
    def role(self):
        if self.is_judge:
            return "judge"

        elif self.is_participant:
            return "participant"

        elif self.is_organizer:
            return "organizer"