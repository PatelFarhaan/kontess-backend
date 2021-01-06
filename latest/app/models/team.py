
from django.db import models
from app.models.user import User

class Team(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    logo = models.FileField(upload_to="team")
    team_mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentor",
        verbose_name="team mentor",
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user"
    )
    team_lead= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user",
        related_name="team_lead",
        null=True,blank=True,
    )
    partipants = models.ManyToManyField('Participant',related_name="team_members")
    created_on = models.DateTimeField(auto_now_add=True)
    team_track= models.ForeignKey('TeamTrack',on_delete=models.CASCADE,related_name="teams",null=True,blank=True)

    def __unicode__(self):
        return self.name




class TeamPortfolio(models.Model):
    docs = models.FileField(upload_to="team")
    team =  models.ForeignKey(Team,on_delete=models.CASCADE,related_name="portfolio")


class TeamTrack(models.Model):
    track_name= models.CharField(max_length=255)
    slug = models.CharField(max_length=255,unique=True)
    description = models.TextField(null=True,blank=True)

    def save(self,*args,**kwargs):
        if self.track_name:
            self.slug= "_".join(self.track_name.lower().split(" "))

        return super().save(*args,**kwargs)


class Invitation(models.Model):
    participants = models.ForeignKey('Participant',on_delete=models.CASCADE,related_name="invites")
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="team")
    status = models.CharField(max_length=50,choices=(("pending","pending"),("rejected","rejected"),("accepted","accepted")))
    created_on= models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="user",related_name="team_invitations")
    email_send= models.BooleanField(default=False)


class TeamEvent(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="event")
    title = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    schedule_date = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="team_event")
    partipants = models.ManyToManyField('Participant',related_name="team_events")
    team_mentor = models.ForeignKey(User,on_delete=models.CASCADE,related_name="mentor_event",null=True,blank=True)

class TeamTask(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="task")
    title = models.CharField(max_length=50)
    description = models.TextField(null=True,blank=True)
    dead_line = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="team_task")
    participants = models.ManyToManyField('Participant',related_name="tasks")


class TeamTaskStatus(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="status")
    team_task = models.ForeignKey('TeamTask',on_delete=models.CASCADE,related_name="task_status",null=True,blank=True)
    status = models.CharField(max_length=50,choices=(("complete","Mark Complete"),("incomplete","Incomplete")),default="incomplete")
    participant = models.ForeignKey('Participant',on_delete=models.CASCADE,related_name="task_status")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class TeamDocs(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,related_name="docs")
    doc_name = models.CharField(max_length=50)
    doc = models.FileField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="team_docs")

