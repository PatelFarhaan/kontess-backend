
import datetime
import calendar
from django.contrib.auth import get_user_model

from app.models.events import Events,EventLogs
from app.models.team import TeamEvent
from app.serializers.team import TeamEventSerializer 
from app.models.participant import Participant
from app.serializers.events import EventSerializer,EventLogSerializer
from app.serializers.user import UserSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions,views
from rest_framework.decorators import action
from django.db.models import Q
from django.db.models.functions import Cast,TruncDate
from django.db.models import F,Func, Value as V
from django.db.models.fields import DateTimeField,DateField
from app.views.notifications import create_notification, EmailAlert

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

User = get_user_model()

from dateutil import parser

class EventsViewsets(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    
    def get_serializer_context(self):
        return {"request":self.request}
    
    def get_queryset(self):
        date = datetime.date.today()
        if self.request.user.is_participant:
            events = Events.objects.filter(attendees__in=["participants","both"],schedule_date__gte=date).order_by("schedule_date")
            return events
        if self.request.user.is_judge:
            return Events.objects.filter(attendees__in=["judges","both"],schedule_date__gte=date).order_by("schedule_date")
        events = Events.objects.filter(schedule_date__gte=date).order_by("schedule_date")
        return events
    
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    def send_email(self, users, event_instance):
        if event_instance.join_url is None or len(event_instance.join_url) ==0:
            return

        email_list = [user.email for user in users]

        date_time_stamp = parser.parse(event_instance.schedule_date)
        dt_str = date_time_stamp.strftime("%d %B %Y %I:%M:%S %p")

        EmailAlert().send_mail(email_list, event_instance.join_url, dt_str)

    def send_email_to_host(self, user, event_instance):
        if event_instance.start_url is None or len(event_instance.start_url) ==0:
            return
        email_list = [user.email]

        date_time_stamp = parser.parse(event_instance.schedule_date)
        dt_str = date_time_stamp.strftime("%d %B %Y %I:%M:%S %p")

        EmailAlert().send_mail_to_host(email_list, event_instance.start_url, dt_str)


    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to add events.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        print(request.data)
        event = Events.objects.create(created_by=request.user,**request.data)
        if event.attendees == 'participants':
            users = User.objects.filter(is_participant=True,is_active=True)
        elif event.attendees == 'judge':    
            users = User.objects.filter(is_judge=True,is_active=True)
        else:
            users = User.objects.filter(Q(is_participant=True,is_active=True)|Q(is_judge=True,is_active=True))
        
        for user in users:
            data={
                "created_for":user,
                "attendees":"participant" if user.is_participant else "judge",
                "event": event
            }
            log = EventLogs.objects.create(created_by=request.user,**data)
            dt={
                        "title":"Admin created a new event - <strong><a href='/dashboard/events'>'{}'</a></strong>".format(event.title),
                        "description":"Admin created a new event - {}".format(event.title),
                        "created_for": user,
                        "type":"response",
                        "req_data":{"event_id":event.id}
            }
            create_notification(dt,request)
        self.send_email(users, event)
        self.send_email_to_host(request.user, event)
            # if user.new_events:
            #     try:
            #         html_message="<html><body><h2>Admin created a new event - {}</h2><div></body></html>".format(event.title,event.schedule_date)
            #         email_message = EmailMultiAlternatives("New Event email",'',settings.EMAIL_HOST_EMAIL,[user.email])
            #         email_message.attach_alternative(html_message, 'text/html')
            #         email_message.send()
            #     except Exception as e:
            #         print(e)
            #         pass

        return Response({"msg":"Event sucessfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Event sucessfuly deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["post"],url_path="edit")    
    def edit(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to add events.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        event = self.get_object()
        
        for key,value in request.data.items():
            setattr(event,key,value)
        event.save()
           
        if event.attendees == 'participants':
            users = User.objects.filter(is_participant=True,is_active=True)
        elif event.attendees == 'judge':    
            users = User.objects.filter(is_judge=True,is_active=True)
        else:
            users = User.objects.filter(Q(is_participant=True,is_active=True)|Q(is_judge=True,is_active=True))
        EventLogs.objects.filter(event=event).delete()

        self.send_email(users, event)
        self.send_email_to_host(request.user, event)

        for user in users:
            data={
                "created_for":user,
                "attendees":"participant" if user.is_participant else "judge",
                "event": event
            }
            log = EventLogs.objects.create(created_by=request.user,**data)

        return Response({"msg":"Event successfully updated.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=False,methods=["get"],url_path="month-wise-event")    
    def month_wise(self,request,*args,**kwargs):
        first_day,last_day=calendar.monthrange(int(request.query_params.get("year")),int(request.query_params.get("month")))
        if len(request.query_params.get("month")) == 1:
            month="0{}".format(request.query_params.get("month"))
        else:
            month = request.query_params.get("month")      
        first_day = "{}-{}-01".format(request.query_params.get("year"),month)
        last_day ="{}-{}-{}".format(request.query_params.get("year"),month,last_day)
        data = Events.objects.filter(schedule_date__gte = first_day,schedule_date__lte = last_day).annotate(day_mod = Cast('schedule_date', DateField())).order_by('day_mod',"-id")
        return Response({"data":self.get_serializer(data,many=True).data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)


        
class EventLogViewsets(viewsets.ModelViewSet):
    serializer_class = EventLogSerializer
    
    def get_queryset(self):
        return EventLog.objects.all()
    

class EventView(views.APIView):
    permission_class = (permissions.IsAuthenticated,)
    def get(self,request,*args,**kwargs):
        date=datetime.date.today()
        data={}
        admin_event = Events.objects.filter(attendees__in=["participants","both"],schedule_date__gte = date).annotate(
           day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
           
        participants = Participant.objects.filter(user=request.user)
        data["admin_event"] = EventSerializer(admin_event,many=True).data
        data["team_event"] = {}
        
        if participants:
            team_events =  TeamEvent.objects.filter(partipants = participants[0])
            data["team_event"] = TeamEventSerializer(team_events,many=True).data
        
        return Response({"data":data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)    