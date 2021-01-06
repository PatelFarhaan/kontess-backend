from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models.task import Task,ParticipantTask
from app.models.team import Team
from app.models.participant import Participant
from app.views.notifications import create_notification
from django.core.mail import EmailMultiAlternatives
from app.models.announcement import AnnouncementStatus
from app.models.notifications import Notification

from django.conf import settings


User = get_user_model()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance,created, **kwargs):
    if created:
        if instance.role == 'participant':
            tasks = Task.objects.filter(assing_to = "individuals").order_by("id")
            participant = Participant.objects.get(user=instance)
            for task in tasks:
                try:
                    ParticipantTask.objects.get(task=task,participant = participant)
                except:
                    ParticipantTask.objects.create(task=task,participant = participant)



@receiver(post_save, sender=Team)
def save_team(sender, instance, created,**kwargs):
    if created:
        tasks = Task.objects.filter(assing_to = "teams").order_by("id")
        for task in tasks:
            try:
                ParticipantTask.objects.get(task=task,team = instance)
            except:
                ParticipantTask.objects.create(task=task,team = instance)



@receiver(post_save, sender=AnnouncementStatus)
def save_team(sender, instance, created,**kwargs):
    if created:
        dt={
            "title":"New announcement is created by admin",
            "description":"New announcement is created by admin",
            "created_for": instance.user,
            "type":"response",
            "req_data":{"ans_ment_id":instance.id}
        }
        Notification.objects.create(created_by=User.objects.filter(is_superuser=True)[0], **dt)

        if instance.user.new_announcement:
            try:
                html_message="<html><body><h2>New announcement '{}' is created by admin. </h2><div></body></html>"
                email_message = EmailMultiAlternatives("Announcement email",'',settings.EMAIL_HOST_EMAIL,[instance.user.email])
                email_message.attach_alternative(html_message, 'text/html')
                email_message.send()
            except Exception as e:
                print(e)
                pass