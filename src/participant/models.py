from django.db import models
from django.contrib.auth.models import User
from team.models import Team

# Create your models here.
class Participant(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )
    graduation_year = models.IntegerField()
    team = models.ForeignKey("team.Team", 
        verbose_name=("participants team"), 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)

class TeamRequest(models.Model):
    essay = models.CharField(("request reason"), max_length=100)
    team = models.ForeignKey(
        Team, 
        verbose_name=("the team that's being requested"), 
        on_delete=models.CASCADE
    )
    participant = models.OneToOneField(
        Participant, 
        verbose_name=("participant"), 
        on_delete=models.CASCADE,
    )
    
    def __unicode__(self):
        return "{0} - #{1} {2} {3}".format(
            self.team.name, 
            self.participant.id,
            self.participant.user.first_name, 
            self.participant.user.last_name
        )