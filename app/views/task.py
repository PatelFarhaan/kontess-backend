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
import calendar,json,datetime
from rest_framework import viewsets,status,permissions,views
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from app.models.participant import Participant
from app.models.team import Team,TeamTrack,TeamTaskStatus
from app.models.task import Task, QuestionsCriteria,ParticipantTask,AssingJudgeToTask,ParticipantTaskdocs,AssingJudgeToTask,TaskGrading,TaskGrades
from app.serializers.task import TaskSerializers,QuestionsCriteriaSerializers,ParticipantTaskSerializer,AssingJudgeToTaskSerializer, \
AssingJudgeToTaskDetailSerializer,TaskGradingSerializers,TaskDetailsSerializer
from app.serializers.team import TeamAdminTaskSerializer,TeamTaskStatusSerializer
from app.views.notifications import create_notification
from django_filters.rest_framework import DjangoFilterBackend
from app.backends.task_filters import TaskFilter
from django.contrib.auth import get_user_model
from django.db.models import Q,Count
from django.db.models.functions import Cast
from django.db.models.fields import DateField,DateTimeField
from app.serializers.user import UserSerializer
User = get_user_model()

class TaskViewsets(viewsets.ModelViewSet):
    serializer_class = TaskSerializers
    filter_backends = (DjangoFilterBackend, )
    filter_class = TaskFilter
    
    def get_queryset(self):
        return Task.objects.order_by("-id")
    
    def get_serializer_context(self):
        return {"request":self.request}
    
    def send_notification(self,obj,request):
        
        if obj.assing_to.lower() == 'teams':
            
            teams = Team.objects.all()
            for team in teams:
                try:
                    ParticipantTask.objects.get(task=obj,team=team)
                except:
                    ParticipantTask.objects.create(task=obj,team=team)
                try:
                    for participant in team.partipants.all():
                        dt={
                            "title":"Admin created a new task for your teams {},".format(team.name),
                            "description":"Admin created a new task for your teams {}.".format(team.name),
                            "created_for": participant.user,
                            "type":"response",
                            "req_data":{}
                        }
            
                        create_notification(dt,request)
                except Exception as e:
                    pass
        else:  
            participants = Participant.objects.filter(user__is_active=True) 
            for participant in participants:
                try:
                    ParticipantTask.objects.get(task=obj,participant=participant)
                except:
                    ParticipantTask.objects.create(task=obj,participant=participant)
                dt={
                    "title":"New task '{}' created by admin to you".format(obj.title),
                    "description":"New task '{}' created by admin to you".format(obj.title),
                    "created_for": participant.user,
                    "type":"response",
                    "req_data":{}
                }
                create_notification(dt,request)
        
    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        questions = request.data.pop("questions")
        obj = Task.objects.create(created_by=request.user,**request.data)
        
        for question in questions:
            try:
                QuestionsCriteria.objects.get(task=obj,created_by=request.user,**question)
            except QuestionsCriteria.DoesNotExist:
                QuestionsCriteria.objects.create(task=obj,created_by=request.user,**question)
        if  obj.status.lower() == "publish":
            self.send_notification(obj,request)
        obj.save()
        return Response({"msg":"Task created sucessfully","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Successfully deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["post"],url_path="update")
    def _update(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        task_state = obj.status
        
        questions = request.data.pop("questions")
        
        for key,value in request.data.items():
            setattr(obj,key,value)
        obj.save()
        
        QuestionsCriteria.objects.filter(task=obj).delete()
        for question in questions:
            try:
                QuestionsCriteria.objects.get(task=obj,created_by=request.user,**question)
            except QuestionsCriteria.DoesNotExist:
                QuestionsCriteria.objects.create(task=obj,created_by=request.user,**question)
                
        if obj.status.lower() == "publish" and task_state.lower() == "draft":
            self.send_notification(obj,request)
            
        return Response({"msg":"Task update sucessfully","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["post"],url_path="judge_assign")
    def judge_assing(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        users = User.objects.filter(id__in=[judge.get('id') for judge in request.data.get("judges")])
        if obj.max_no_of_judge == AssingJudgeToTask.objects.filter(created_by=request.user,task=obj).count():
            return Response({"msg":"You can't assing more judges to this task.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_200_OK)
        track = None
        if not (request.query_params.get("assing_to") == "individuals"):
            track = TeamTrack.objects.filter(id=request.data.get("track"))
            if not track:
                return Response({"msg":"Please set a track for judge assing.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
            track= track[0]
        for user in users:
            try:
                ajt=AssingJudgeToTask.objects.get(judge=user,created_by=request.user)
            except AssingJudgeToTask.DoesNotExist:
                ajt=AssingJudgeToTask.objects.create(judge=user,created_by=request.user)
                
            ajt.task.add(obj)
            if not (request.query_params.get("assing_to") == "individuals"):
                ajt.track.add(track)
            ajt.save()
            
            dt={
                "title":"New task assing {} to you".format(obj.title),
                "description":"Task assing",
                "type":"response",
                "created_for":ajt.judge,
                "req_data":{}   
            }
            create_notification(dt,request)
            
        return Response({"msg":"Judges are assing to this task","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["post"],url_path="judge_remove")
    def judge_remove(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = self.get_object()
        user = User.objects.get(id=request.data.get("judge_id"))
        if not (request.query_params.get("assing_to") == "individuals"):
            track = TeamTrack.objects.filter(id=request.data.get("track"))
            if not track:
                return Response({"msg":"Please set a track for judge assing.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
            track = track[0]
            st = AssingJudgeToTask.objects.filter(judge=user,created_by=request.user,task=obj,track = track).delete()
            if st:
                dt={
                    "title":"You have been remove as judge from task".format(obj.title),
                    "description":"Task Removed",
                    "type":"response",
                    "created_for":user,
                    "req_data":{}   
                }
                create_notification(dt,request)
                return Response({"msg":"Successfully remove judge from this task.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        else:
            st = AssingJudgeToTask.objects.filter(judge=user,created_by=request.user,task=obj).delete()
            if st:
                dt={
                    "title":"You have been remove as judge from task".format(obj.title),
                    "description":"Task Removed",
                    "type":"response",
                    "created_for":user,
                    "req_data":{}   
                }
                create_notification(dt,request)
                return Response({"msg":"Successfully remove judge from this task.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
                
        return Response({"msg":"Judge is not remove from task.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True,methods=["post"],url_path="grading")
    def judge_grading(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        dt={
            "task":obj,
            "judge":request.user,
            "over_all_comments":request.data.get("over_all_comments",None),
            "status":request.data.get("status",None)
            ,"grade":ParticipantTask.objects.get(id=request.data.get("submitted_task_id"))
        }
        if request.data.get("task_type") == "teams":
            dt.update({"team":Team.objects.get(id=request.data.get("id"))})
        else:
            dt.update({"participant":Participant.objects.get(id=request.data.get("id"))})
        grade = TaskGrading.objects.create(**dt)
        for question in request.data.get("questions"):
            TaskGrades.objects.create(grade=grade,questions_id=question.get("id"),score=question.get("score"),comment=question.get("comment",None))
                
        return Response({"msg":"Grading to task sucessfully {}".format(request.data.get("status",None)),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["post"],url_path="update-grading")
    def judge_update_grading(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        grd_obj = TaskGrading.objects.filter(task=obj,id=request.query_params.get("grade_id"))

        if not grd_obj:
            return Response({"msg":"No grade found for this task","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        grd_obj = grd_obj[0]

        grd_obj.over_all_comments = request.data.get("over_all_comments") 
        grd_obj.status = request.data.get("status")
        grd_obj.save()
        TaskGrades.objects.filter(grade=grd_obj).delete()
        for question in request.data.get("questions"):
            TaskGrades.objects.create(grade=grd_obj,questions_id=question.get("id"),score=question.get("score"),comment=question.get("comment",None))
        return Response({"msg":"Grading update sucessfully {}".format(request.data.get("status",None)),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=False,methods=["get"],url_path="assigned-teams")
    def judge_assing_task(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = Task.objects.filter(id=request.query_params.get("task_id"))
        if not obj:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        assing_task = AssingJudgeToTask.objects.filter(task=obj,judge=request.user).order_by("-id")
        if not assing_task:
            return Response({"msg":"No task assigned to this judge","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        teams=[]
        for ts in assing_task:
            for tr in ts.track.all():
                for i in tr.teams.all():
                    teams.append(i)
        count = len(teams)
        teams=teams[int(request.query_params.get("offset",0)):int(request.query_params.get("limit",10))+int(request.query_params.get("offset",0))]
        judges = [task.judge for task in AssingJudgeToTask.objects.filter(task=obj)]   
        serializer = TeamAdminTaskSerializer(teams, many=True,context={"request":request,"task":obj})
        return Response({"data":{"teams":serializer.data,"count":count,"judges":UserSerializer(judges,many=True).data},"status":status.HTTP_200_OK},status=status.HTTP_200_OK)  

    @action(detail=True,methods=["post"],url_path="release-score")
    def release_score(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = self.get_object()
        obj.release_score_to_participant = request.data.get("release_score_to_participant")
        obj.save()
        ptasks = ParticipantTask.objects.filter(task=obj,status__in=["submit","resubmit"])
        for ptask in ptasks:
            data = {
                "title":"Your score is released for a task {}".format(obj.title),
                "description":"Your score is released for a task {}".format(obj.title),
                "type":"response",
                "created_for":ptask.participant.user,
                "req_data":{}   
            }
            create_notification(data,request) 
            
        return Response({"msg":"Release score to participant status update succesfully","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
    @action(detail=False,methods=["get"],url_path="submission-status")
    def progress_bar(self,request,*args,**kwargs):
        now=datetime.datetime.today()
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskDetailsSerializer(page, many=True,context={"request":request})
            return self.get_paginated_response(serializer.data)
 
        serializer = TaskDetailsSerializer(queryset, many=True,context={"request":request})
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        
        
        
        
class ParticipantTaskViewset(viewsets.ModelViewSet):
    serializer_class = ParticipantTaskSerializer
    permissions_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        if self.request.user.is_participant:
            participant_task = ParticipantTask.objects.filter(participant__user=self.request.user)
            teams = Team.objects.filter(partipants__user=self.request.user)
            team_tasks = ParticipantTask.objects.filter(team__in=teams)
            tsk = participant_task | team_tasks
            return tsk.distinct().order_by("-id") 
        return ParticipantTask.objects.distinct().order_by('-id')
    
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        tasks = AssingJudgeToTask.objects.filter(task=instance.task)
        judges = UserSerializer([task.judge for task in tasks],context={"request":request},many=True).data
        
        return Response({"data":serializer.data,"judges":judges,"status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
    
    def get_serializer_context(self):
        return {"request":self.request}
    
    @action(detail=True,methods=["post"],url_path="update")
    def _update(self,request,*args,**kwargs):
        if not request.user.is_participant:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        obj = self.get_object()
        for key,value in request.data.items():
            setattr(obj,key,value)
            
        if request.FILES.getlist("doc",None):
            ParticipantTaskdocs.objects.filter(task=obj).delete()
                
            for d in request.FILES.getlist("doc"): 
                ParticipantTaskdocs.objects.create(doc=d,task=obj)
                
        obj.submitted_by = request.user    
        obj.save()
        
        return Response({"msg":"Task sucessfully submited","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=False,methods=["get"],url_path="month-wise-listing")
    def listing(self,request,*args,**kwargs):
        if not request.user.is_authenticated:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
         
        first_day,last_day=calendar.monthrange(int(request.query_params.get("year")),int(request.query_params.get("month")))
        if len(request.query_params.get("month")) == 1:
            month="0{}".format(request.query_params.get("month"))
        else:
            month = request.query_params.get("month")      
        first_day = "{}-{}-01".format(request.query_params.get("year"),month)
        last_day ="{}-{}-{}".format(request.query_params.get("year"),month,last_day)
        
        if request.user.is_participant:
            task_list = ParticipantTask.objects.filter(task__submission_due_date__gte=first_day,task__submission_due_date__lte=last_day,participant__user=request.user).order_by("id")
            queryset = self.filter_queryset(task_list)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True,context={"request":request})
                return self.get_paginated_response(serializer.data)
     
            serializer = self.get_serializer(queryset, many=True,context={"request":request})
            return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        elif request.user.is_judge:
            task_list = AssingJudgeToTask.objects.filter(judge=request.user).order_by("id")
            queryset = self.filter_queryset(task_list)
            page = self.paginate_queryset(queryset)

            if page is not None:
                dt = [] 
                for i in page:
                    for j in i.task.all():
                        dt.append(j)  
                serializer = TaskSerializers(dt, many=True,context={"request":request})
                dt=[]
                for i in serializer.data:
                    dt.append({"task": i})
                return self.get_paginated_response(dt)
            dt = [] 
            for i in queryset:
                for j in i.task.all():
                    dt.append(j)  
            serializer = TaskSerializers(dt, many=True,context={"request":request})
            dt=[]
            for i in serializer.data:
                dt.append({"task": i})
            return Response({"data":dt,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        else:
            task_list = Task.objects.filter(submission_due_date__gte=first_day,submission_due_date__lte=last_day).order_by("id")
            queryset = self.filter_queryset(task_list)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TaskSerializers(page, many=True,context={"request":request})
                dt=[]
                for i in serializer.data:
                    dt.append({"task":i})
                return self.get_paginated_response(dt)
     
            serializer = TaskSerializers(queryset, many=True,context={"request":request})
            dt=[]
            for i in serializer.data:
                dt.append({"task":i})
            return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=["get"],url_path="individual-tasks")      
    def get_individual_task(self,request,*args,**kwargs):
        if not (request.user.is_superuser or request.user.is_judge):
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        task = Task.objects.filter(id=kwargs.get("pk"))
        if not task:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        
        task = task[0]
        judges = [task.judge for task in AssingJudgeToTask.objects.filter(task=task,task__assing_to="individuals").order_by("id")]
        participants = ParticipantTask.objects.filter(task=task,task__assing_to="individuals")
        count=len(participants)
        participants = participants[int(request.query_params.get("offset",0) or 0):int(request.query_params.get("limit",10) or 10)+int(request.query_params.get("offset",0) or 0)] 
        serializer = self.get_serializer(participants, many=True,context={"request":request})    
        return Response({"data":{"individuals":serializer.data,"judges":UserSerializer(judges,context={"request":request},many=True).data},"count":count,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
      
    @action(detail=False,methods=["get"],url_path="judge-task")
    def judge_task_listing(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        assing_task = AssingJudgeToTask.objects.filter(judge =  request.user).order_by("-id")
        task_list = []
        for task in assing_task:
            for t in task.task.all():
                task_list.append(t)
        count=len(task_list)
        if request.query_params.get("limit",'10') and request.query_params.get("offset","0"):
            task_list = task_list[int(request.query_params.get("offset",'0')):int(request.query_params.get("limit","0"))+int(request.query_params.get("offset",'0'))]
        
        return Response({"data":TaskSerializers(task_list,many=True,context={"request":request}).data,"count":count,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)    

    @action(detail=False,methods=['get'],url_path="todo-list")
    def todo_list(self,request,*args,**kwargs):
        now = datetime.datetime.today().isoformat()
        if request.user.is_participant:
            admin_tasks = ParticipantTask.objects.filter(status="pending",participant__user = request.user,task__submission_due_date__gte=now)
            team_tasks = ParticipantTask.objects.filter(status="pending",team__partipants = Participant.objects.get(user=request.user),task__submission_due_date__gte=now)
            admin_tasks= admin_tasks|team_tasks
            admin_tasks= admin_tasks.distinct().order_by("-id")
            queryset = self.filter_queryset(admin_tasks)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ParticipantTaskSerializer(page, many=True,context={"request":request})
                return self.get_paginated_response(serializer.data)
     
            serializer = ParticipantTaskSerializer(queryset, many=True,context={"request":request})
            return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)   
            
        if request.user.is_judge:
            
            judge_tasks = AssingJudgeToTask.objects.filter(judge=request.user)
            tasks = []
            for judge_task in judge_tasks:
                for task in judge_task.task.all():
                    tasks.append(task)
                    
            judge_tasks = Task.objects.filter(id__in=[task.id for task in tasks],submission_due_date__lte=now,grade_due_date__gte=now).distinct().order_by("-id")  
            queryset = self.filter_queryset(judge_tasks)
            page = self.paginate_queryset(queryset)
            if page is not None:
                ts=[]
                serializer = TaskSerializers(page, many=True,context={"request":request})
                
                for i in serializer.data:
                    ts.append({"task":i})
                return self.get_paginated_response(ts)
     
            serializer = TaskSerializers(queryset, many=True,context={"request":request})
            for i in serializer.data:
                ts.append({"task":i})
            return Response({"data":ts,"status":status.HTTP_200_OK },status=status.HTTP_200_OK) 
          
        return Response({"msg":"No task found.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)        
    
class TaskGradingViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskGradingSerializers
    
    def get_queryset(self):
        return TaskGrading.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)  
     


    