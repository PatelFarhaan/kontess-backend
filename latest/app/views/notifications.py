import os
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets,views
from rest_framework.decorators import action
from app.models.notifications import Notification
from app.serializers.notifications import NotificationSerializer
from django.db.models import Count
from django.core.files.storage import FileSystemStorage

import requests

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


class ChatUploadedView(views.APIView):
    def post(self,request,*args,**kwargs):
        dir_path=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        myfile = request.FILES.get('file')
        fs = FileSystemStorage(location=os.path.join(dir_path,'media/chat-docs/')) #defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)
        file_url = fs.url(filename)
        return Response({"data":{"file_url":request.build_absolute_uri("/media/chat-docs/{}".format(filename))},'status':status.HTTP_200_OK},status=status.HTTP_200_OK)


class EmailAlert(object):
    def __init__(self):
        pass

    def __chunk_it(self, items, chunk_size=100):
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]

    def send_request(self, url, body, method="POST",  headers=None):

        payload = body
        if headers is None:
            headers = {'Content-Type': 'application/json' }

        response = requests.request(method, url, headers=headers, json=payload)
        if response.status_code != 200:
            print("error", response.text)
        else:
            print("email sent",response.json())


    def send_mail(self, email_list, event_link, date_time_stamp):

        url = "https://demo.kontess.com/zoom/common-email"

        email_chunk_list = self.__chunk_it(email_list)

        for each_chunk in email_chunk_list:

            body = {
                "email":each_chunk,
                "link":event_link,
                "datetime":date_time_stamp,
            }

            self.send_request(url, body=body)


    def send_mail_to_host(self, email_list, event_link, date_time_stamp):

        url = "https://demo.kontess.com/zoom/host-email"

        body = {
            "email":email_list,
            "link":event_link,
            "datetime":date_time_stamp,
        }

        self.send_request(url, body=body)





