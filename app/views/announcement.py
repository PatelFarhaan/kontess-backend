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
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model 
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets

from app.models.announcement import Announcement,AnnouncementStatus
from app.serializers.announcement import AnnouncementSerializer,AnnouncementStatusSerializer
from rest_framework.decorators import action

User = get_user_model()

class AnnouncementViewsets(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        return Announcement.objects.all()
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        announcement = Announcement.objects.create(created_by=request.user,**request.data)
        if announcement.announcement_type == 'participants':
            users = User.objects.filter(is_active=True,is_participant=True)
        elif announcement.announcement_type == 'judges':   
            users = User.objects.filter(is_active=True,is_judge=True)
        else:
            users = User.objects.all()
        for user in users:
            try:
                AnnouncementStatus.objects.get(announcement=announcement,user=user)
            except AnnouncementStatus.DoesNotExist:
                AnnouncementStatus.objects.create(announcement=announcement,user=user)
                
        return Response({"msg":"Annoucement successfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)   
            
class AnnouncementStatusViewsets(viewsets.ModelViewSet):
    serializer_class = AnnouncementStatusSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        return AnnouncementStatus.objects.filter(user=self.request.user)
    
    @action(methods=["patch"],detail=True,url_path='update')
    def _update(self,request,pk=None):
        if request.user.is_anonymous:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        announcementStatus = get_object_or_404(AnnouncementStatus,pk=pk)
        if announcementStatus.is_star:
            announcementStatus.is_star=False;
        else:
            announcementStatus.is_star=True;
            
        announcementStatus.is_read=True
        announcementStatus.save()
        return Response({"msg":"You have sucessfuly update a annoucement.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    