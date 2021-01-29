from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.deletion import SET_NULL
from app.models.events import Events
from app.models.participant import Participant
from app.models.team import TeamTrack,Team

User = get_user_model()

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True,blank=True)
    submission_due_date = models.CharField(max_length=255)
    grade_due_date  = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="tasks")
    max_no_of_judge = models.PositiveIntegerField(default=0)
    assing_to = models.CharField(max_length=50,choices=(("teams","teams"),("individuals","individuals")),default="teams")
    status = models.CharField(max_length=50,choices=(("Draft","Draft"),("Publish","Publish")),null=True,blank=True)
    release_score_to_participant = models.BooleanField(default=False)
    is_randomized = models.BooleanField(default=False)
    event = models.ForeignKey(Events, on_delete=models.SET_NULL, related_name="events", default=None, null=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return "{}({})".format(self.title,self.id)

class TaskLock(models.Model):
    task =  models.ForeignKey(Task,on_delete=models.CASCADE,related_name="lock",null=True,blank=True)
    track = models.ForeignKey(TeamTrack,on_delete=models.CASCADE,related_name="task_lock",null=True,blank=True)
    lock = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

# TODO Merge RandomJudgeToTaskAndTeam, AssingJudgeToTask together by flag
class RandomJudgeToTaskAndTeam(models.Model):
    task =  models.ForeignKey(Task,on_delete=models.CASCADE,related_name="random_judges",null=True,blank=True)
    track = models.ForeignKey(TeamTrack,on_delete=models.CASCADE,related_name="random_judges",null=True,blank=True)
    team =  models.ForeignKey(Team,on_delete=models.CASCADE,related_name="random_team",null=True,blank=True)
    judge = models.ForeignKey(User,on_delete=models.CASCADE,related_name="random_judges",null=True,blank=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="_random_judges")

    class Meta:
        ordering = ['-id']

class QuestionsCriteria(models.Model):
    task =  models.ForeignKey(Task,on_delete=models.CASCADE,related_name="questions")
    track = models.ForeignKey(TeamTrack,related_name="questions_assign_to_track",null=True,blank=True, on_delete=models.CASCADE)
    question = models.CharField(max_length=50,null=True,blank=True)
    max_score = models.PositiveIntegerField(default=0)
    feedback = models.BooleanField(default=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="questions")


class AssingJudgeToTask(models.Model):
    task =  models.ManyToManyField(Task,related_name="judge_assign")
    track = models.ManyToManyField(TeamTrack,related_name="judge_assign_to_track", blank=True)
    judge = models.ForeignKey(User,on_delete=models.CASCADE,related_name="judge_assign")
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="admin_assign")
    assign_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['assign_date']


class ParticipantTask(models.Model):
    task =  models.ForeignKey(Task,on_delete=models.CASCADE,related_name="participant_task",null=True,blank=True)
    team =  models.ForeignKey(Team,on_delete=models.CASCADE,related_name="participant_task_team",null=True,blank=True)
    participant = models.ForeignKey(Participant,on_delete=models.CASCADE,related_name="participant_task",null=True,blank=True)
    description = models.TextField(null=True,blank=True)
    status = models.CharField(max_length=50,default="pending",choices=(("pending","pending"),("submitted","submit"),("resubmit","resubmit")))
    submitted_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="task_submitted",null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class ParticipantTaskdocs(models.Model):
    doc = models.FileField(upload_to = "task",null=True,blank=True)
    task =  models.ForeignKey(ParticipantTask,on_delete=models.CASCADE,related_name="submitted_docs",null=True,blank=True)
    submitted_date = models.CharField(max_length=255,null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)


class TaskGrading(models.Model):
    task =  models.ForeignKey(Task,on_delete=models.CASCADE,related_name="task_grading",null=True,blank=True)
    team =  models.ForeignKey(Team,on_delete=models.CASCADE,related_name="team_task_grading",null=True,blank=True)
    participant = models.ForeignKey(Participant,on_delete=models.CASCADE,related_name="participant_task_grading",null=True,blank=True)
    grade = models.ForeignKey(ParticipantTask,on_delete=models.CASCADE,related_name="task_grading",null=True,blank=True)
    judge = models.ForeignKey(User,on_delete=models.CASCADE,related_name="judge_grades",null=True,blank=True)
    over_all_comments = models.TextField(null=True,blank=True)
    status = models.CharField(max_length=50,choices=(("Draft","Draft"),("Publish","Publish")),null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)


class TaskGrades(models.Model):
    grade = models.ForeignKey(TaskGrading,on_delete=models.CASCADE,related_name="grades",null=True,blank=True)
    questions =  models.ForeignKey(QuestionsCriteria,on_delete=models.CASCADE,related_name="task_grading",null=True,blank=True)
    score = models.PositiveIntegerField(default=0)
    comment = models.CharField(max_length=255,null=True,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
