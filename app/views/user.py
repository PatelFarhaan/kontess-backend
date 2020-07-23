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
import json
from functools import reduce
import operator
from django.db.models import Q

from datetime import date

from app.models.user import User,UserSkills,LinkExpiration,ManageRegistration
from app.models.judge import Judge,JudgeRequest
from app.models.organizer import Organizer
from app.models.participant import Participant
from app.views.notifications import create_notification

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route, action
from app.serializers.user import UserSerializer, LoginSerializer, UserIdSerializer,UserSkillSerializer,ManageRegistrationSerializer
from app.serializers.judge import JudgeSerializer
from app.serializers.organizer import OrganizerSerializer
from app.serializers.participant import ParticipantDetailSerializer

from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives,send_mail
from django.contrib.auth.hashers import make_password
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Count

class UserViewSet(viewsets.ModelViewSet):
    """
    user/
    """
    
    serializer_class = UserSerializer
    serializers = {'login': LoginSerializer,
                   'approve_registration': UserIdSerializer}
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'create_team_request': [permissions.IsAuthenticated],
                                    'registration_requests': [permissions.IsAuthenticated],
                                    'forgotpasswordemail':[permissions.AllowAny],
                                    'reset_password':[permissions.AllowAny]
                                    }
    
    queryset = User.objects.order_by("-id")
    team_id = None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        role=request.query_params.get("role",None);
        if not role:
            return Response({"msg":"Please set a role to view list.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        data,search,self.team_id = {},{},None
        if role == "admin":
            data.update({"is_active":True,"is_superuser":True})
        elif role == 'organizer':
            data.update({"is_active":True,"is_organizer":True})
        elif role == 'judge':
            data.update({"is_active":True,"is_judge":True})    
        elif role == 'participant':
            data.update({"is_active":True,"is_participant":True})   
        else:
            data={} 
        if request.query_params.get("name",None):
            search.update({"username__icontains":request.query_params.get("name",None),"full_name__icontains":request.query_params.get("name",None)})
            
        if request.query_params.get("skill",None):
            data.update({"skill":UserSkills.objects.get(value=request.query_params.get("skill"))})
            
        queryset = self.filter_queryset(self.get_queryset().filter(**data))
        if search:
            queryset = queryset.filter(reduce(operator.or_, (Q(**d) for d in [dict([i]) for i in search.items()])))
        
        if request.query_params.get("team_id",None):
            self.team_id=request.query_params.get("team_id")   

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True,context=_context or self.get_serializer_context()).data
        
       
        return Response({"data":serializer,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
              
    def get_serializer_context(self):
        return {'request': self.request,'team_id':self.team_id}
    
    @action(detail=False, methods=['post'])
    def signup(self, request):
        data={}
        role = request.data.get('role', None)
        if role not in ["judge", "organizer", "participant"]:
            data.update=({
                "status": status.HTTP_400_BAD_REQUEST,
                "msg": "incorrect role"
                }
            )
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        try:
            limit=ManageRegistration.objects.all()
            limit=limit[0]
            if limit.status:
                if not (limit.reg_date > date.today()):
                    return Response({"msg":"Registration has been closed. Please contact your administrator.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
                if role == "judge":
                    judge_count = User.objects.values("is_judge").filter(is_judge=True).annotate(count=Count("is_judge"))
                    if judge_count[0].get("count") >= limit.judge_count:
                        return Response({"msg":"Deadline passed for registration as judge. Please contact your administrator.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
                if role == "participant":
                    participant_count = User.objects.values("is_participant").filter(is_participant=True).annotate(count=Count("is_participant"))
                    if participant_count[0].get("count") >= limit.participant_count:
                        return Response({"msg":"Deadline passed for registration as participant. Please contact your administrator.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            pass       
        
        try:
            user = User.objects.get(email=request.data.get("email"))
            if user.is_judge:
                jr = JudgeRequest.objects.get(judge__user=user)
                if jr.status == "pending":
                    return Resposne({"msg":"Your request is pending waiting for a admin approvel.","status":status.HTTP_304_NOT_MODIFIED},status=status.HTTP_304_NOT_MODIFIED)
                if jr.status == "rejected":
                    return Resposne({"msg":"Your request is rejected by admin.","status":status.HTTP_406_NOT_ACCEPTABLE},status=status.HTTP_406_NOT_ACCEPTABLE)
                if jr.status == "approved":
                   return Resposne({"msg":"Your request is approved by admin. Please Login to continue. ","status":status.HTTP_406_NOT_ACCEPTABLE},status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            print(e)
            pass
        
        skill_set = request.data.pop("skill",None)
        
        serializer = UserSerializer(data=request.data,context={"request":self.request})
        if serializer.is_valid():
            user = serializer.save()
        else:
            data.update(
                    {
                        "status":status.HTTP_400_BAD_REQUEST,
                        "msg":serializer.errors,
                    })
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if role == "judge":
            user.is_judge = True
            user.is_active = False
            if skill_set:
                for s_set in UserSkills.objects.filter(id__in=[skill.get("id") for skill in skill_set]):
                    user.skill.add(s_set)
                    
            judge = Judge.objects.create(user=user)
            judge.save()
            jr = JudgeRequest.objects.create(judge=judge,created_for=User.objects.filter(is_superuser=True)[0])
            jr.save()
            user.save()
            request.user = user
            
            data={
                "title":"New join request as judge by {} . Waiting for admin approvel.".format(user.full_name),
                "description":"New Join Request For judge",
                "created_for": User.objects.filter(is_superuser=True)[0],
                "type":"judge-request",
                "req_data":{"judge_id":user.id,"judge_rq_id":jr.id}
            }
            create_notification(data,request)
#            
            return Response({"msg":"You have been successfully registered!. Please wait for the admin approval.","status":status.HTTP_200_OK}, status=status.HTTP_200_OK)

        elif role == "organizer":
            user.is_organizer = True
            user.is_active = True
            organizer = Organizer.objects.create(user=user)
            organizer.save()
            user.save()
            data.update(
                    {
                        "status":status.HTTP_200_OK,
                        #"data":OrganizerSerializer(organizer).data
                        "msg":"Please check your email and activate your account."
                    })
            msg = settings.USER_ACTIVATE_URL.format(user.id)
            LinkExpiration.objects.create(url=msg)
            html_message="<html><body><h2>Please click here to verify your account.</h2><div><a href='{}'>{}</a></div></body></html>".format(msg,msg)
            email_message = EmailMultiAlternatives("Kontess Account Activation email",'',settings.EMAIL_HOST_USER,[user.email])
            email_message.attach_alternative(html_message, 'text/html')
            email_message.send()
            return Response(data, status=status.HTTP_200_OK)

        elif role == "participant":
            user.is_participant = True
            user.is_active = False
            participant = Participant.objects.create(user=user)
            participant.save()
            user.save()
            # data.update(
            #         {
            #             "status":status.HTTP_200_OK,
            #             #"data":ParticipantDetailSerializer(participant).data
            #             "msg":"Please check your email and activate your account."
            #         })
            # msg = settings.USER_ACTIVATE_URL.format(user.id)
            # LinkExpiration.objects.create(url=msg)
            # html_message="<html><body><h2>Please click here to verify your account.</h2><div><a href='{}'>{}</a></div></body></html>".format(msg,msg)
            # email_message = EmailMultiAlternatives("Kontess Account Activation email",'',settings.EMAIL_HOST_USER,[user.email])
            # email_message.attach_alternative(html_message, 'text/html')
            # email_message.send()
            return Response(data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        data={}
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"msg":"Username or password incorrect","status":status.HTTP_401_UNAUTHORIZED})
        
        
        payload = UserSerializer(user,context={"request":self.request}).data
        if user.is_active:
            login(request, user)
            
            payload = UserSerializer(user,context={"request":self.request}).data

            token = str(RefreshToken.for_user(user).access_token)
            payload["token"] = token
            
            data.update(
                {
                    "status":status.HTTP_200_OK,
                    "msg":"login sucessfull",
                    "data":payload
                })
            return Response(data,status=status.HTTP_200_OK)           
                
        else:
            data.update(
                {
                    "status":status.HTTP_403_FORBIDDEN,
                    "msg":"user is not active, please contact administrator",
                    "data":payload
                })
            return Response(data,status=status.HTTP_403_FORBIDDEN)          

    @action(detail=False, methods=['get'])
    def registration_requests(self, request):
        data={}
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            organizers = Organizer.objects.filter(user__is_active=False)
            organizers = OrganizerSerializer(organizers, many=True).data

            judges = Judge.objects.filter(user__is_active=False)
            judges = JudgeSerializer(judges, many=True).data
            
            data.update(
                    {
                        "status":status.HTTP_200_OK,
                        "msg":"registration request",
                        "data":{"organizers": organizers, "judges": judges}
                    })
            return Response(data,status=status.HTTP_200_OK)           
                    
    @action(detail=False, methods=['get'])
    def activate(self, request):
        data={}
        
        try:
            user_id = request.query_params.get('user_id', None)
            link = LinkExpiration.objects.filter(url=settings.USER_ACTIVATE_URL.format(user_id))
            if not link:
                return Response({"msg":"your link is not valid","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
            link=link[0]
            if link.is_expired:
                return Response({"msg":"your link has been expired",'status':status.HTTP_403_FORBIDDEN},status= status.HTTP_403_FORBIDDEN)
            link.is_expired=True
            link.save()
            
            user = User.objects.get(id=user_id)
            if user.is_active:
                return Response({"msg":"User Already active","status":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user.is_active = True
                user.is_staff = True
                user.save()
                return Response({"msg":"User active sucessfuly","status":status.HTTP_200_OK})
        except User.DoesNotExist:
            return Response({"msg":"User not found.","status":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def forgotpasswordemail(self,request):
        ##To send mail
            user=self.get_queryset().filter(email=request.data.get("email"))
            if not user:
                return Response({
                    'msg': "Email does not exist",
                    "status": status.HTTP_401_UNAUTHORIZED,
                }) 
                
            user=user[0]
                
            current_site = get_current_site(request)
            site_name = current_site.name
            activation_link = settings.PASSWORD_RESET_URL.format(user.id)
            LinkExpiration.objects.create(url=activation_link)

            message = "Hello {0},\n {1}".format(user.username, activation_link)

            mail_subject = 'Reset your account.'
            to_email = request.data.get('email')

            try:   
                send_mail(mail_subject, message, recipient_list=[to_email], from_email=settings.EMAIL_HOST_USER)
            except Exception as e:
                print(e)
                pass
            
            response = {
                    'msg': "Email has been send to your email id. please click to reset your password",
                    'status' : status.HTTP_200_OK, 
                    'activation_link': activation_link,
                    'to_email':to_email,
            }
            return Response(response)
        
    @action(detail=False, methods=['post'])
    def reset_password(self,request,*args,**kwargs):
        data = request.data
        
        link = LinkExpiration.objects.filter(url=settings.PASSWORD_RESET_URL.format(data.get("id")))
        if not link:
            return Response({"msg":"your link is not valid","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        link=link[0]
        if link.is_expired:
            return Response({"msg":"your link has been expired",'status':status.HTTP_403_FORBIDDEN},status= status.HTTP_403_FORBIDDEN)
        link.is_expired=True
        link.save()
                
        user=self.get_queryset().filter(id=data.get("id"))
        if not user:
            return Response({
                'msg': "User does not exist",
                "status": status.HTTP_400_BAD_REQUEST,
            }) 
        user = user[0]    
        user.set_password(data.get('password'))
        user.save(update_fields=("password",))
        return Response({"msg":"Your password update successfuly",'status' : status.HTTP_200_OK},status=status.HTTP_200_OK) 
    
    
    @action(detail=False, methods=['post'])
    def edit_profile(self,request):
        data = request.data
        data =  {"full_name":data.get("full_name"),"email":data.get("email"),"biography":data.get("biography") if data.get("biography",None) else ""}
        
        if request.user.email != data.get("email"):
            users = User.objects.filter(email=data.get("email"))
            if users:
                return Response({"msg":"User already exist with given email id.","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
            
        if request.data.get("user_image",None):
            data.update({"user_image":request.data.get("user_image",None)})
        
        user = request.user
        for attr,value in data.items():
            setattr(user, attr, value)
            
        if request.data.get("skill",None):
            user.skill.clear()
            for s_set in UserSkills.objects.filter(id__in=[skill.get("id") for skill in json.loads(request.data.get("skill"))]):
                user.skill.add(s_set)
        user.save()
        
        return Response({"data":self.get_serializer(user).data,"msg":"Profile updated successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
    
    
    @action(detail=False, methods=['get'])
    def listing(self,request):
        users = User.objects.filter(is_active=True)
        judges,participant={"count":0},{"count":0}
        data={"judge":[],"participant":[],"organizer":[],"admin":[]}
        for user in users:
            if user.is_superuser:
                data["admin"].append(self.get_serializer(user).data)
            elif user.is_judge:
                 
                data["judge"].append(self.get_serializer(user).data)
            elif user.is_participant:
                data["participant"].append(self.get_serializer(user).data)
            elif user.is_organizer:
                data["organizer"].append(self.get_serializer(user).data)
            else:
                pass
             
        if request.user.is_superuser:
            dte=date.today()
            judges = User.objects.filter(is_active=True,is_judge=True,created_on__gte=dte).values('is_judge').annotate(count=Count("id"))
            if judges:
                judges=judges[0]
                 
            participant = User.objects.filter(is_active=True,is_participant=True,created_on__gte=dte).values('is_participant').annotate(count=Count("id"))
            if participant:
                participant=participant[0]    
                 
            data.update({
                "judges_count":len(data.get("judge")),
                "participant_count":len(data.get("participant")),
                "organizer_count":len(data.get("organizer")),
                "judge_join_today":judges.get('count',0) if judges else 0,
                "participant_join_today":participant.get('count',0) if participant else 0,
            })
           
        return(Response({"status":status.HTTP_200_OK,"data":data},status=status.HTTP_200_OK))  
    
    @action(detail=True, methods=['post'],url_path="edit-user")
    def user_edit(self,request,pk=None):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to update user","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        data =  {"full_name":data.get("full_name"),"email":data.get("email"),"biography":data.get("biography") if data.get("biography",None) else ""}
        
        if request.data.get("user_image",None):
            data.update({"user_image":request.FILES.get("user_image")})
            
        user = User.objects.get(id=pk)
        
        if user.email != data.get("email"):
            users = User.objects.filter(email=data.get("email"))
            if users:
                return Response({"msg":"User already exist with given email id.","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
            
        for attr,value in data.items():
            setattr(user, attr, value)
            
        if request.data.get("skill",None):
            user.skill.clear()
            for s_set in UserSkills.objects.filter(id__in=[skill.get("id") for skill in json.loads(request.data.get("skill"))]):
                user.skill.add(s_set)
                
        user.save()
        
        return Response({"data":self.get_serializer(user).data,"msg":"Profile updated successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
    
    @action(detail=True,methods=['delete','post'],url_path="delete-user")
    def user_delete(self,request,pk=None):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to detete user","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        user = User.objects.get(id=pk)
        user.delete()
        return Response({"msg":"Deleting a user sucessfuly done.","status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
        
#     def updatepassword(self,request):     
#               
#  
#         if serializer.is_valid(raise_exception=True):
#             user_data = User.objects.filter(email=request.user.email)
#              
#             for user in user_data:
#                 for field in serializer.data:
#                     if field == 'password':
#                         setattr(user, field, make_password(serializer.data[field]))
#     
#                 user.save()
#         response = {
#                 'data': serializer.data,
#             'status_code' : 200,  
#                 'url' : request.path,
#                 }
#                           
#         return Response(response)   
    
    @action(detail=False,methods=["post"],url_path="add-user")
    def add_user(self,request):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to detete user","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        data =  {"full_name":data.get("full_name"),"email":data.get("email"),"biography":data.get("biography") if data.get("biography",None) else ""}
        
        users = User.objects.filter(Q(email=data.get("email"))|Q(username=data.get("username")))
        if users:
            return Response({"msg":"User already exist with given email id.","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
            
        if request.data.get("user_image",None):
            data.update({"user_image":request.FILES.get("user_image",None)})
            
        user = User()
        for attr,value in data.items():
            setattr(user, attr, value)
        user.save()
        
        msg = settings.USER_ACTIVATE_URL.format(user.id)
        html_message="<html><body><h2>Please click here to verify your account.</h2><div><a href='{}'>{}</a></div></body></html>".format(msg,msg)
        email_message = EmailMultiAlternatives("Kontess Set password email",'',settings.EMAIL_HOST_USER,[user.email])
        email_message.attach_alternative(html_message, 'text/html')
        email_message.send()
        return Response({"data":self.get_serializer(user).data,"msg":"New User is created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
        
    def get_serializer_class(self):
        if self.action in self.serializers:
            return self.serializers[self.action]

        return UserSerializer

class TokenView(TokenObtainPairView):
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        data={
            "status": status.HTTP_200_OK,
            "data": serializer.validated_data
        }
        return Response(data, status=status.HTTP_200_OK)
    
class UserSkillViewsets(viewsets.ModelViewSet):
    serializer_class = UserSkillSerializer
    permissions_classes =(permissions.AllowAny,)
    
    def get_queryset(self):
        return UserSkills.objects.all()

class ManageRegistrationViewsets(viewsets.ModelViewSet):
    serializer_class = ManageRegistrationSerializer
    permissions_classes =(permissions.AllowAny,)
    
    def get_queryset(self):
        return ManageRegistration.objects.all()
    
    @action(detail=False, methods=['get','post'])
    def myconfig(self, request):
        if not request.user.is_superuser:
            return Response({"msg":"Your are not authorized to access this.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        try:
            mr = ManageRegistration.objects.get(created_by=request.user)
        except ManageRegistration.DoesNotExist:
           mr = ManageRegistration.objects.create(created_by=request.user)
           
        if request.method == "POST":
            for key,value in request.data.items():
                setattr(mr,key,value)
            mr.save()
            return Response({"msg":"Deadline updated sucessfully ","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        return Response({"data":ManageRegistrationSerializer(mr).data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    