from django.db import models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name
