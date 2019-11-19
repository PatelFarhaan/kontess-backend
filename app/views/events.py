'''
/**
 *@copyright : ToXSL Technologies Pvt. Ltd. < www.toxsl.com >
 *@author     : Shiv Charan Panjeta < shiv@toxsl.com >
 *
 * All Rights Reserved.
 * Proprietary and confidential :  All information contained herein is, and remains
 * the property of ToXSL Technologies Pvt. Ltd. and its partners.
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 *
 *
 */
'''
import datetime
from django.contrib.auth import get_user_model

from app.models.events import Events,EventLogs
from app.serializers.events import EventSerializer,EventLogSerializer
from app.serializers.user import UserSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from django.db.models import Q
from django.db.models.functions import Cast
from django.db.models.fields import DateField

User = get_user_model()

class EventsViewsets(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    
    def get_serializer_context(self):
        return {"request":self.request.user}
    
    def get_queryset(self):
        date = datetime.date.today()
        if self.request.user.is_participant:
            return Events.objects.filter(attendees__in=["participants","both"],schedule_date__gte = date).annotate(
               day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
        if self.request.user.is_judge:
            return Events.objects.filter(attendees__in=["judges","both"],schedule_date__gte = date).annotate(
               day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
        return Events.objects.order_by('-id')
    
    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to add events.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
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
                
        return Response({"msg":"Event sucessfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)


class EventLogViewsets(viewsets.ModelViewSet):
    serializer_class = EventLogSerializer
    
    def get_queryset(self):
        return EventLog.objects.all()
    
    
    
    