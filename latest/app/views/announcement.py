
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model 
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Q

from app.models.announcement import Announcement,AnnouncementStatus
from app.serializers.announcement import AnnouncementSerializer,AnnouncementStatusSerializer
from app.views.notifications import create_notification
from rest_framework.decorators import action
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

User = get_user_model()

class AnnouncementViewsets(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        return Announcement.objects.order_by("-id")
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            dt=[]
            for i in serializer.data:
                dt.append({"announcement":i})
                
            return self.get_paginated_response(dt)

        serializer = self.get_serializer(queryset, many=True)
        dt=[]
        for i in serializer.data:
            dt.append({"announcement":i})
        return Response(dt)
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        announcement = Announcement.objects.create(created_by=request.user,**request.data)
        if announcement.announcement_type == 'participants':
            announcement.announcement_type = "participants"
            users = User.objects.filter(is_active=True,is_participant=True)
        elif announcement.announcement_type == 'judges':
            announcement.announcement_type = "judges"   
            users = User.objects.filter(is_active=True,is_judge=True)
        else:
            announcement.announcement_type = "every_one"
            users = User.objects.filter(Q(is_participant=True)|Q(is_judge=True),is_active=True)
        for user in users:
            try:
                AnnouncementStatus.objects.get(announcement=announcement,user=user)
            except AnnouncementStatus.DoesNotExist:
                AnnouncementStatus.objects.create(announcement=announcement,user=user)
                    
        return Response({"msg":"Annoucement successfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)   
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":{"announcement":serializer.data},"status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Announcement successfully deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)   
    
    @action(methods=["post"],detail=True,url_path='update')
    def _update(self,request,pk=None):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj=self.get_object()
        
        for key,value in request.data.items():
            setattr(obj,key,value)
        obj.save()
        return Response({"msg":"Announcement updated successfully.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        
class AnnouncementStatusViewsets(viewsets.ModelViewSet):
    serializer_class = AnnouncementStatusSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        _star={}
        if self.request.query_params.get("is_star",None) == "true":
            _star = {"is_star":True}
            
        if self.request.user.is_superuser:
            return AnnouncementStatus.objects.filter(**_star).order_by("-id")
        
        return AnnouncementStatus.objects.filter(user=self.request.user,**_star).order_by("-id")
    
    @action(methods=["patch"],detail=True,url_path='update')
    def _update(self,request,pk=None):
        if request.user.is_anonymous:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        announcementStatus = get_object_or_404(AnnouncementStatus,pk=pk)
        if request.data.get("is_star"):
            announcementStatus.is_star = True
        else:
            announcementStatus.is_star = False 
            
        announcementStatus.is_read = True
        announcementStatus.save()
        return Response({"msg":"You have sucessfuly update a annoucement.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    