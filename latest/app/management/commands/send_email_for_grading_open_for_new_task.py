from django.utils import timezone
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from app.models.task import ParticipantTask,AssingJudgeToTask
from django.db.models.functions import Cast
from django.db.models.fields import DateField
from app.models.notifications import Notification 
from django.contrib.auth import get_user_model

User = get_user_model()

def get_participants_task():
    date = timezone.now().date() + timedelta(days=7)
    tasks = ParticipantTask.objects.annotate(day_mod=Cast('task__submission_due_date', DateField()),distinct=True).annotate(
        grade_day_mod=Cast('task__grading_due_date', DateField()),distinct=True).filter(status__in["submitted","resubmit"],day_mod__lt= date,grade_day_mod__gt=date)
    return tasks

def get_admin_user():
    return User.objects.filter(is_superuser=True)[0]

def get_judges(task):
    return [ajt.judge for ajt in AssingJudgeToTask.objects.filter(task=task)]
    

def email_sending(data,users):
    for user in users:
        if user.grading_open:
            email_message = EmailMultiAlternatives(data.get("title"),data.get("description"),settings.EMAIL_HOST_EMAIL,[user.email])
            email_message.attach_alternative(html_message, 'text/html')
            email_message.send()
    return True

def create_notification(task):
    dt={
        "title":"Grading is open on this task {}".format(task.task.title),
        "description":"Grading is open on this task {}".format(task.task.title),
    }
    return email_sending(dt,get_judges(task.task))

class Command(BaseCommand):
    def handle(self, *args, **options):
        if get_participants_task():
            for task in get_participants_task():
                create_notification(task)
            print("Email genrated successfully")    
        else:
            print("No task found.") 