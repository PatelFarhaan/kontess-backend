from django.utils import timezone
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from app.models.task import ParticipantTask
from django.db.models.functions import Cast
from django.db.models.fields import DateField
from app.models.notifications import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def get_participants_task():
    date = timezone.now().date()
    tasks = ParticipantTask.objects.annotate(day_mod=Cast('task__submission_due_date', DateField())).filter(status="pending",day_mod=date)
    return tasks

def get_admin_user():
    return User.objects.filter(is_superuser=True)[0]

def email_sending(data,user):
    if user.task_due_today:
        email_message = EmailMultiAlternatives(data.get("title"),data.get("description"),settings.EMAIL_HOST_EMAIL,[user.email])
        email_message.attach_alternative(html_message, 'text/html')
        email_message.send()
    return True

def create_notification(task):
    dt={
        "title":"Your submisstion is due today on this task {}".format(task.task.title),
        "description":"Your submisstion is due today on this task {} plese submit as soon as possible".format(task.task.title),
    }
    return email_sending(dt,task.participant.user)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if get_participants_task():
            for task in get_participants_task():
                create_notification(task)
            print("Email and notification genrated successfully")
        else:
            print("No task found.")