from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from app.models.notifications import Notification
from app.serializers.notifications import NotificationSerializer
from django.db.models import Count


def create_notification(data,request):
    try:
        notification = Notification.objects.get(created_by=request.user,**data)
    except Notification.DoesNotExist:
        notification = Notification.objects.create(created_by=request.user,**data)
    return notification




class NotificationViewsets(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        if self.request.user:
            return Notification.objects.filter(created_for=self.request.user).order_by("-created_on").order_by("-id")
        else:
            return Notification.objects.order_by("-created_on")
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def create(self,request,*args,**kwargs):
        return create_notification(request.data,self.request)
    
    @action(detail=False, methods=['post'],url_path="update")
    def _update(self,request,*args,**kwargs):
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        notifications = Notification.objects.filter(created_for=self.request.user,is_seen=True)
        for notification in notifications:
            notification.is_seen = False
            notification.save()
        total_count = Notification.objects.filter(created_for=self.request.user).values("is_seen").annotate(count=Count("id"))    
        unseen_count = Notification.objects.filter(created_for=self.request.user,is_seen=True).values("is_seen").annotate(count=Count("id"))
        return Response({
            "data":{"total_count":total_count[0].get("count") if total_count else 0,"unseen_count":unseen_count[0].get("count") if unseen_count else 0},
            "status":status.HTTP_200_OK
        },status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'],url_path="count")
    def notification_count(self,request,*args,**kwargs): 
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        total_count = Notification.objects.filter(created_for=self.request.user).values("is_seen").annotate(count=Count("id"))    
        unseen_count = Notification.objects.filter(created_for=self.request.user,is_seen=True).values("is_seen").annotate(count=Count("id"))
        return Response({
            "data":{"total_count":total_count[0].get("count") if total_count else 0,"unseen_count":unseen_count[0].get("count") if unseen_count else 0},
            "status":status.HTTP_200_OK
        },status=status.HTTP_200_OK)
    
    
    
    