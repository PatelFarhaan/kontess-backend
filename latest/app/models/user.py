from django.contrib.auth.models import AbstractUser
from django.db import models


class UserSkills(models.Model):
    label = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)

    def save(self,*args,**kwargs):
        if self.label:
            self.value = '_'.join(self.label.lower().split(' '))
            return super().save(*args,**kwargs)

class User(AbstractUser):

    full_name = models.CharField(max_length=100, default="")
    user_image = models.FileField(upload_to="profile",null=True,blank=True)
    phone_number = models.CharField(max_length=100, null=True,blank=True)
    school_name = models.CharField(max_length=100, null=True,blank=True)
    major = models.CharField(max_length=100, null=True,blank=True)
    affiliations = models.CharField(max_length=100, null=True,blank=True)
    i_agree_to_the_rules_of_the_competition = models.BooleanField('terms_condition', default=False)

    biography = models.TextField(null=True,blank=True)
    is_judge = models.BooleanField('judge status', default=False)
    is_participant = models.BooleanField('participant status', default=False)
    is_organizer = models.BooleanField('organizer status', default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    skill =  models.ManyToManyField(UserSkills,related_name="skills")

#Notification settings
    new_announcement= models.BooleanField(default=False)
    new_events = models.BooleanField(default=False)
#Judge
    grading_open = models.BooleanField(default=False)
    grading_due_today = models.BooleanField(default=False)
    assing_as_mentor = models.BooleanField(default=False)
    mentor_request_approved_status = models.BooleanField(default=False)
#participant
    new_task = models.BooleanField(default=False)
    task_due_today = models.BooleanField(default=False)
    result_is_posted =  models.BooleanField(default=False)
    team_join_request = models.BooleanField(default=False)
    invited_join_request = models.BooleanField(default=False)
    approve_join_request = models.BooleanField(default=False)
    team_events = models.BooleanField(default=False)
    team_tasks = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["-id"]

    @property
    def role(self):
        if self.is_judge:
            return "judge"

        elif self.is_participant:
            return "participant"

        elif self.is_organizer:

            return "organizer"

        elif self.is_superuser:
            return "admin";

class LinkExpiration(models.Model):
    url = models.URLField()
    is_expired = models.BooleanField(default=False)
    created_on= models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-created_on']


class ManageRegistration(models.Model):
    judge_count = models.PositiveIntegerField(default=0)
    participant_count = models.PositiveIntegerField(default=0)
    status = models.BooleanField(default=False)
    reg_date = models.DateField(null=True,blank=True)

    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="user_mangement")
    created_on = models.DateTimeField(auto_now_add=True)



