

from django.contrib.auth import authenticate, login,get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, action
from app.backends.admin_access import AdminAuthenticationPermission

from app.models.judge import Judge,JudgeRequest,TeamMentorRequest,JudgeRequestTeam
from app.models.team import Team
from app.serializers.judge import JudgeSerializer,JudgeRequestSerializer,TeamMentorRequestSerializer,JudgeRequestTeamSerializer
from app.serializers.user import UserSerializer
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from app.backends.judge_filter import JudgeRequestFilter
from django.core.mail import EmailMultiAlternatives
from app.models.notifications import Notification
from app.views.notifications import create_notification 
from django.conf import settings

User = get_user_model()
# Create your views here.
class JudgeViewSet(viewsets.ModelViewSet):
    serializer_class = JudgeSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated]}
    queryset = Judge.objects.all()
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    
    def create(self, request):
        serializer = UserSerializer(data=request.data,context={"request":self.request})
        if serializer.is_valid():
            user = serializer.save()
            j = Judge.objects.create(
                user=user
            )
            j.save()
            return Response(JudgeSerializer(j).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        serializer = JudgeSerializer(self.queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        judge = get_object_or_404(self.queryset, pk=pk)
        serializer = JudgeSerializer(judge)
        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                judge = get_object_or_404(self.queryset, user=user)
                return Response(
                    JudgeSerializer(judge).data, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
class JudgeRequestViewsets(viewsets.ModelViewSet):
    serializer_class =  JudgeRequestSerializer
    permission_classes =  (AdminAuthenticationPermission,)
    
    filter_backends = (DjangoFilterBackend, )
    filter_class = JudgeRequestFilter
    
    def get_serializer_context(self):
        return {"request":self.request}
    
    def get_queryset(self):
        if self.request.query_params.get("name",None):
            return JudgeRequest.objects.filter(
                judge__in=Judge.objects.filter(user__in=User.objects.filter(full_name__icontains=self.request.query_params.get("name")))).order_by("-id")
        
        return JudgeRequest.objects.order_by("-id")
    
    @action(detail=True, methods=["post"], url_path="update")
    def _update(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        obj.status = request.data.get("status")
        obj.save()
        
        if obj.status == "approved":
            obj.judge.user.is_active = True
            obj.judge.user.is_judge = True
            obj.judge.user.save()
        else:
            obj.judge.user.is_active = False
            obj.judge.user.is_judge = True
            obj.judge.user.save()
        try:
            html_message="<html><body><h2>Your account as a judge is {} by admin. Please proceeds to login. </h2><div></body></html>".format(request.data.get("status"))
            email_message = EmailMultiAlternatives("Kontess Judge Account email",'',settings.EMAIL_HOST_EMAIL,[obj.judge.user.email])
            email_message.attach_alternative(html_message, 'text/html')
            email_message.send()
        except Exception as e:
            print(e)
            pass
        Notification.objects.filter(type="judge-request").delete()
        return Response({"msg":"Judge/Coach request updated sucessfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
class TeamMentorRequestViewsets(viewsets.ModelViewSet):
    serializer_class = TeamMentorRequestSerializer
    
    def get_queryset(self):
        if self.request.query_params.get("status",None):
            if self.request.user.is_superuser:
                dt={"admin_status": self.request.query_params.get("status")}
            elif self.request.user.is_judge:
                dt={"for_judge":self.request.user,"judge_status":self.request.query_params.get("status")}
            return TeamMentorRequest.objects.filter(**dt).order_by("-id")
        
        return TeamMentorRequest.objects.order_by("-id")
    
    @action(detail=True,methods=["post"],url_path="update")
    def _update_status(self,request,*args,**kwargs):
        user_type = None
        mentor = TeamMentorRequest.objects.filter(id = kwargs.get("pk"))
        if not mentor:
            return Response({"msg":"Mentor request not found.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        mentor=mentor[0]
        if request.user.is_superuser:
            mentor.admin_status = request.data.get("status")
            Notification.objects.filter(type="mentor-request",created_for=mentor.for_admin).delete()
            user_type = "admin"
        elif request.user.is_judge:
            mentor.judge_status = request.data.get("status")
            Notification.objects.filter(type="mentor-request",created_for=mentor.for_judge).delete()
            user_type = "judge"
        else:
            return Response({"msg":"You are not authorized user.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        if request.data.get("status") == "approved" and request.user.is_superuser:
            mentor.team.team_mentor = mentor.for_judge
            mentor.team.save()
            
        mentor.save()
        if mentor.admin_status == request.data.get("status") and mentor.judge_status ==  request.data.get("status") :
            try:
                participants = mentor.team.partipants
                for participant in participants:
                    dt={
                        "title":"Your request for a team mentor has been {} by {}".format(request.data.get("status"),user_type),
                        "description":"Your request for a team mentor has been {} by {}".format(request.data.get("status"),user_type),
                        "created_for": participant.user,
                        "type":"mentor-status",
                        "req_data":{"mentor_request_id":mentor.id}
                    }
                    create_notification(dt,request)
            except Exception as e:
                print(e)
                pass
        return Response({"msg":"Mentor request updated sucessfuly by {}.".format(user_type),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
class JudgeRequestTeamViewsets(viewsets.ModelViewSet):   
    serializer_class = JudgeRequestTeamSerializer
    
    def get_queryset(self):
        return JudgeRequestTeam.objects.all()
    
    @action(detail=True,methods=["patch"],url_path="update")
    def jrt_update(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to access this.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        obj.status = request.data.get("status")
        obj.save()
        dt = {
            "title":"Your request for join team {} as judge/coach has been {} by admin".format(obj.team.name,request.data.get("status")),
            "description":"Your request for join team {} as judge/coach has been {} by admin".format(obj.team.name,request.data.get("status")),
            "created_for": obj.judge.user,
            "type":"response",
            "req_data":{}
        }
        create_notification(dt,request)
        if obj.judge.user.mentor_request_approved_status:
            try:
                html_message="<html><body><h2>Your request for join team {} as judge/coach has been {} by admin.</h2><div></body></html>".format(obj.team.name,request.data.get("status"))
                email_message = EmailMultiAlternatives("Admin {} you request as team mentor".format(request.data.get("status")),'',settings.EMAIL_HOST_EMAIL,[obj.judge.user.email])
                email_message.attach_alternative(html_message, 'text/html')
                email_message.send()
            except Exception as e:
                print(e)
                pass
        if request.data.get("status") ==  "approved":
            obj.team.team_mentor = obj.judge.user
            obj.team.save()

            try:
                for participant in obj.team.partipants:
                    dt = {
                        "title":"Judge {} join team mentor of your team {} {} by admin".format(obj.judge.user.full_name,obj.team.name,request.data.get("status")),
                        "description":"Judge {} join team mentor of your team {} {} by admin".format(obj.judge.user.full_name,obj.team.name,request.data.get("status")),
                        "created_for": participant.user,
                        "type":"response",
                        "req_data":{}
                    }
                    create_notification(dt,request)
            except Exception as e:
                print(e)
                pass
            Notification.objects.filter(type="judge-request-team",created_for=request.user).delete()
        return Response({"msg":"Judge request updated successfully by admin.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        
        
        