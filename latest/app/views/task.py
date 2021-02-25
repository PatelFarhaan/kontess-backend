from app.models.judge import Judge
from app.models.events import Events
from functools import reduce
import calendar,json,datetime,os,csv,xlsxwriter,random,datetime
from rest_framework import viewsets,status,permissions,views
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from app.models.participant import Participant
from app.models.team import Team,TeamTrack,TeamTaskStatus, TeamTask
from app.models.task import Task, QuestionsCriteria,ParticipantTask,AssingJudgeToTask,ParticipantTaskdocs,TaskGrading,TaskGrades,RandomJudgeToTaskAndTeam,TaskLock
from app.models.user import User as UserModal

from app.serializers.task import TaskSerializers,QuestionsCriteriaSerializers,ParticipantTaskSerializer,AssingJudgeToTaskSerializer, \
AssingJudgeToTaskDetailSerializer,TaskGradingSerializers,TaskDetailsSerializer
from app.serializers.team import TeamAdminTaskSerializer, TeamSerializer,TeamTaskStatusSerializer, TeamSerializerTaskDetails
from app.views.notifications import create_notification
from django_filters.rest_framework import DjangoFilterBackend
from app.backends.task_filters import TaskFilter
from django.contrib.auth import get_user_model
from django.db.models import Q,Count
from django.db.models.functions import Cast
from django.db.models.fields import DateField,DateTimeField
from app.serializers.user import UserSerializer

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

User = get_user_model()

def avg(lst):
    tv=[i for i in lst if i !=0]

    try:
        avg=sum(lst)/len(tv)
    except ZeroDivisionError as z:
        avg=0
    return avg

class TaskViewsets(viewsets.ModelViewSet):
    serializer_class = TaskSerializers
    filter_backends = (DjangoFilterBackend,)
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
                            "title":"Admin created a new task <strong><a href='/dashboard/task/'>'{0}' </a></strong> for your teams <strong><a href='/dashboard/team_view/{1}'>'{2}'</a></strong>".format(obj.title,team.id,team.name),
                            "description":"Admin created a new task for your teams {}.".format(team.name),
                            "created_for": participant.user,
                            "type":"response",
                            "req_data":{}
                        }

                        create_notification(dt,request)
                        if participant.user.new_task:
                            try:
                                html_message="<html><body><h2>Admin created a new task <strong><a href='/dashboard/task/'>'{0}' </a></strong> for your teams <strong><a href='/dashboard/team_view/{1}'>'{2}'</a></strong></h2><div></body></html>".format(obj.title,team.id,team.name)
                                email_message = EmailMultiAlternatives("New Task",'',settings.EMAIL_HOST_EMAIL,[participant.user.email])
                                email_message.attach_alternative(html_message, 'text/html')
                                email_message.send()
                            except Exception as e:
                                print(e)
                                pass
                except Exception as e:
                    pass
        else:
            participants = Participant.objects.all()
            for participant in participants:
                try:
                    ParticipantTask.objects.get(task=obj,participant=participant)
                except:
                    ParticipantTask.objects.create(task=obj,participant=participant)
                dt={
                    "title":"New task <strong><a href='/dashboard/task'>'{}'</a></strong> created by admin to you".format(obj.title),
                    "description":"New task '{}' created by admin to you".format(obj.title),
                    "created_for": participant.user,
                    "type":"response",
                    "req_data":{}
                }
                create_notification(dt,request)
                if participant.user.new_task:
                    try:
                        html_message="<html><body><h2>New task '{}' created by admin to you</h2><div></body></html>".format(obj.title)
                        email_message = EmailMultiAlternatives("New Task",'',settings.EMAIL_HOST_EMAIL,[participant.user.email])
                        email_message.attach_alternative(html_message, 'text/html')
                        email_message.send()
                    except Exception as e:
                        print(e)
                        pass

    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        questions = request.data.pop("questions")
        eventid = request.data.pop("event", None)
        if eventid is not None and eventid:
            request.data["event"] = Events.objects.get(id=eventid)

        obj = Task.objects.create(created_by=request.user,**request.data)

        for question in questions:
            track = question.get("track", "null")
            if track == "null":
               question["track"] = None
            elif type(track) == str  and len(track)>0:
                track = int(track)
                question["track"] = TeamTrack.objects.filter(id=track)[0]

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
        eventid = request.data.pop("event", None)
        if eventid is not None and eventid:
            request.data["event"] = Events.objects.get(id=eventid)
        else:
            request.data["event"] = None

        for key,value in request.data.items():
            setattr(obj,key,value)
        obj.save()

        qcr=QuestionsCriteria.objects.filter(task=obj)

        # if len(qcr) != len(questions):
        #         qcr[len(qcr)-1].delete()

        for index,question in enumerate(questions):
            track = question.get("track", "null")
            if track == "null":
               question["track"] = None
            elif type(track) == str  and len(track)>0:
                track = int(track)
                question["track"] = TeamTrack.objects.filter(id=track)[0]

            task_obj = None
            try:
                task_obj=QuestionsCriteria.objects.get(task=obj,created_by=request.user,**question)
            except QuestionsCriteria.DoesNotExist:
                task_obj=QuestionsCriteria.objects.create(task=obj,created_by=request.user,**question)

            try:
                for key,value in question.items():
                    setattr(task_obj,key,value)
                task_obj.save()
            except:
                pass

        if obj.status.lower() == "publish" and task_state.lower() == "draft":
            self.send_notification(obj,request)

        return Response({"msg":"Task update sucessfully","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=["post"],url_path="judge_assign")
    def judge_assing(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        obj = self.get_object()
        users = User.objects.filter(id__in=[judge.get('id') for judge in request.data.get("judges")])
        # if obj.max_no_of_judge == AssingJudgeToTask.objects.filter(created_by=request.user,task=obj).count():
        #     return Response({"msg":"You can't assign more judges to this task.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_200_OK)
        track = None
        if not (request.query_params.get("assing_to") == "individuals"):
            track = TeamTrack.objects.filter(id=request.data.get("track"))
            if not track:
                return Response({"msg":"Please set a track for judge assign.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
            track= track[0]
        for user in users:
            try:
                ajt=AssingJudgeToTask.objects.get(task=obj,judge=user,created_by=request.user)
            except AssingJudgeToTask.DoesNotExist:
                ajt=AssingJudgeToTask.objects.create(judge=user,created_by=request.user)
                ajt.task.add(obj)
            if not (request.query_params.get("assing_to") == "individuals"):
                ajt.track.add(track)
            ajt.save()

            if request.query_params.get("assing_to") == "individuals":
                dt={
                    "title":"New task assign {} to you".format(obj.title),
                    "description":"Task assign",
                    "type":"response",
                    "created_for":ajt.judge,
                    "req_data":{}
                }
                create_notification(dt,request)

        return Response({"msg":"Judges are assign to this task","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=["post"],url_path="judge_remove")
    def judge_remove(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = self.get_object()
        user = User.objects.get(id=request.data.get("judge_id"))
        if not (request.query_params.get("assing_to") == "individuals"):
            track = TeamTrack.objects.filter(id=request.data.get("track"))
            if not track:
                return Response({"msg":"Please set a track for judge assign.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
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
            tg=TaskGrades()
            if question.get("score"):
                tg.score = question.get("score")
            else:
                tg.score = 0
            tg.grade=grade
            tg.questions_id=question.get("id")
            tg.comment=question.get("comment",None)
            tg.save()
        return Response({"msg":"Grading to task sucessfully {}".format(request.data.get("status",None)),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=["post"],url_path="live-grading")
    def live_judge_grading(self,request,*args,**kwargs):
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
            particinpant = None
            user = User.objects.get(id=request.data.get("id"))
            try:
                particinpant =Participant.objects.get(user=user)
            except Exception as err:
                Participant.objects.create(user=user)

            dt.update({"participant":particinpant})
        grade = TaskGrading.objects.create(**dt)
        for question in request.data.get("questions"):
            tg=TaskGrades()
            if question.get("score"):
                tg.score = question.get("score")
            else:
                tg.score = 0
            tg.grade=grade
            tg.questions_id=question.get("id")
            tg.comment=question.get("comment",None)
            tg.save()
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
            tg=TaskGrades()
            if question.get("score"):
                tg.score = question.get("score")
            else:
                tg.score = 0
            tg.grade=grd_obj
            tg.questions_id=question.get("id")
            tg.comment=question.get("comment",None)
            tg.save()
        return Response({"msg":"Grading update sucessfully {}".format(request.data.get("status",None)),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=False,methods=["get"],url_path="assigned-teams")
    def judge_assing_task(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = Task.objects.filter(id=request.query_params.get("task_id"))
        if not obj:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        rndjt=RandomJudgeToTaskAndTeam.objects.filter(task=obj,judge=request.user).order_by("-id")

        track = request.query_params.get("track", None)
        if track is not None and len(track)>0:
            track = int(track)
            rndjt=rndjt.filter(track=track)

        teams=[team.team for team in rndjt]

        assing_task = AssingJudgeToTask.objects.filter(task=obj,judge=request.user).order_by("-id")

        track = request.query_params.get("track", None)
        if assing_task and track is not None and len(track)>0:
            track = int(track)
            assing_task=assing_task.filter(track=track)

        # if not assing_task:
        #     return Response({"msg":"No task assigned to this judge","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        # teams=[]
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
                "created_for":ptask.submitted_by,
                "req_data":{}
            }
            create_notification(data,request)
            if ptask.submitted_by.result_is_posted:
                try:
                    html_message="<html><body><strong>Your score is released for a task {}</strong></strong><div></body></html>".format(obj.title)
                    email_message = EmailMultiAlternatives("Score Published",'',settings.EMAIL_HOST_EMAIL,[ptask.submitted_by.email])
                    email_message.attach_alternative(html_message, 'text/html')
                    email_message.send()
                except Exception as e:
                    print(e)
                    pass

        return Response({"msg":"Release score to participant status update succesfully","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=False,methods=["get"],url_path="submission-status")
    def progress_bar(self,request,*args,**kwargs):
        now = datetime.datetime.today()
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskDetailsSerializer(page, many=True,context={"request":request})
            return self.get_paginated_response(serializer.data)

        serializer = TaskDetailsSerializer(queryset, many=True,context={"request":request})
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=["get"],url_path="export")
    def export_task_to_csv(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        obj = self.get_object()
        ptasks = ParticipantTask.objects.filter(task=obj)

        if obj.assing_to == 'teams':
            judges = AssingJudgeToTask.objects.filter(task=obj)

            grades = TaskGrading.objects.filter(task=obj, judge__in = [judge.judge for judge in judges])#.exclude(status="Draft")

            sta={}
            headers={}
            for ptask in ptasks.filter(team__isnull=False):
                total_score = []
                members=[]
                for i in ptask.team.partipants.all():
                    if i.user == ptask.team.team_lead:
                        members.append("{} (leader)".format(i.user.full_name))
                    else:
                       members.append("{}".format(i.user.full_name))

                if  not ptask.team.team_track.track_name in sta:
                    sta.update({ptask.team.team_track.track_name:[]})

                dta = {
                    "Team Name":ptask.team.name,
                    "Track Name":ptask.team.team_track.track_name,
                    "Member list":",".join(members),
                    "Submit Date": ptask.updated_on.strftime("%m/%d/%Y %H:%M %p")
                }

                for index,val in enumerate(judges.filter(track=ptask.team.team_track)):
                    score = []
                    _grades = grades.filter(team=ptask.team, judge=val.judge) #grade=ptask,

                    if _grades:
                        _grades=_grades[0]
                        for _grade in _grades.grades.all():
                            score.append(int(_grade.score))
                        dta.update({"Judge {}".format(index+1): sum(score) if sum(score) != 0 else "" })
                    else:
                        score.append(0)
                        dta.update({"Submit Date":"Did not submit"})
                        dta.update({"Judge {}".format(index+1): "-"})

                    total_score.append(sum(score))
                dta.update({"Average Score":avg(total_score) if avg(total_score) != 0 else ""})
                headers.update({ptask.team.team_track.track_name:[i for i in dta.keys()]})
                sta[ptask.team.team_track.track_name].append(dta)

            kt = {}
            for key,users in sta.items():
                if not key in kt:
                    kt.update({key:[]})
                kt[key].append(headers.get(key))
                for user in users:
                    t = []
                    for i,j in user.items():
                        t.append(j)
                    kt[key].append(t)
            try:
                filename = "/media/csv/task.xlsx"
                file_path= "{}{}".format(os.path.abspath(os.curdir),filename)
                workbook = xlsxwriter.Workbook(file_path)
                for key,vals in kt.items():
                    key="_".join("_".join(key.split("/")).split(" "))
                    worksheet = workbook.add_worksheet(key)
                    row=0
                    for data in tuple(vals):
                        col=0
                        for dt in data:
                            worksheet.write(row, col, str(dt))
                            col += 1
                        row += 1
                workbook.close()
            except Exception as e:
                print(e)
                return Response({"msg":"Task cannot be exported.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        else:
            judges = AssingJudgeToTask.objects.filter(task=obj)
            grades = TaskGrading.objects.filter(task=obj,judge__in = [judge.judge for judge in judges])
            dt = []
            for ptask in ptasks:
                if ptask.participant==None:
                    continue
                total_score = []
                submit_date = ""
                if ptask.updated_on.strftime("%m/%d/%Y %H:%M %p")==ptask.participant.user.created_on.strftime("%m/%d/%Y %H:%M %p"):
                    submit_date = "Did not submit"
                else:
                    submit_date = ptask.updated_on.strftime("%m/%d/%Y %H:%M %p") + " UTC"
                dta = {
                    "Participant Name":ptask.participant.user.full_name,
                    "Submit Date": submit_date
                }
                _grades = grades.filter(grade = ptask)
                if _grades:
                    for index,grade in enumerate(_grades):
                        score = []
                        for _grade in grade.grades.all():
                            score.append(int(_grade.score))

                        total_score.append(sum(score))
                        dta.update({"Judge {}".format(index+1):sum(score) if score else 0})
                else:
                    #dta.update({"Submit Date":"Did not submit"})
                    for index,val in enumerate(judges):
                        dta.update({"Judge {}".format(index+1): "-"})
                        total_score.append(0)

                dta.update({"Total Score":sum(total_score)})
                dt.append(dta)
            try:
                filename = "/media/csv/task.csv"
                file_path= "{}{}".format(os.path.abspath(os.curdir),filename)
                with open(file_path,'w') as file:
                    writer = csv.DictWriter(file,fieldnames=dt[0].keys())
                    writer.writeheader()
                    for user in dt:
                        writer.writerow(user)
                    file.close()
            except Exception as e:
                print(e)
                return Response({"msg":"Task cannot be exported.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

        return Response({"data":{"csv_link":request.build_absolute_uri(filename)},"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    def rnd_assign(self,obj,judges,team,track,request):
        for judge in judges:# .filter(track=track)[random.randrange(0, len(judges.filter(track=track))):len(judges.filter(track=track))]
            try:
                RandomJudgeToTaskAndTeam.objects.get(task=obj,team=team,judge=judge) # judge.judge
            except RandomJudgeToTaskAndTeam.DoesNotExist as e:
                ajt = RandomJudgeToTaskAndTeam.objects.create(judge=judge,team=team,created_by=request.user)
                ajt.task = obj
                ajt.save()
            # if obj.max_no_of_judge == RandomJudgeToTaskAndTeam.objects.filter(task=obj,team=team).count():
            #     break

        return True

    def rnd_teams(self,obj,judges,tracks,request):
        for track in tracks:
            # if judges.filter(track=track).count() > 0:
            try:
                teams = track.teams.all()
            except:
                teams = []
            for team in teams:
                ptask = ParticipantTask.objects.filter(team=team,task=obj)

                if ptask:
                    # ptask = ptask[0]
                    # if ptask.status in ["submit","resubmit","submitted"]:
                    count = 0
                    count = RandomJudgeToTaskAndTeam.objects.filter(task=obj,team=team).count()
                    while count :
                        self.rnd_assign(obj,judges,team,track,request)
                        count -= 1
                                # if obj.max_no_of_judge == RandomJudgeToTaskAndTeam.objects.filter(task=obj,team=team).count():
                                #     break
                                # elif obj.max_no_of_judge != RandomJudgeToTaskAndTeam.objects.filter(task=obj,team=team).count():
                                #     if count == 10:
                                #         if AssingJudgeToTask.objects.filter(task=obj,track=track).count() < obj.max_no_of_judge:
                                #             break
                                # count = count+1

        return True

    @action(detail=True,methods=["post"],url_path="random-judge-assing")
    def random_judges(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not an authorized user.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)


        obj = self.get_object()
        lock = TaskLock.objects.filter(task=obj)
        if lock:
            lock=lock[0]
            if lock.status:
                return Response({"msg":"Your task is locked.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

        RandomJudgeToTaskAndTeam.objects.filter(task=obj).delete()
        TaskGrading.objects.filter(task=obj).delete()
        judges = AssingJudgeToTask.objects.filter(task=obj)
        # TODO: Comment above code & Add random assign to task logic
        # judges = User.objects.filter(is_judge=True)

        if not judges:
            return Response({"msg":"Please assigned juges to this task.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

        tracks= TeamTrack.objects.all()
        self.rnd_teams(obj,judges,tracks,request)
        obj.is_randomized = True
        obj.save()
        for judge in list(set([rjt.judge for rjt in RandomJudgeToTaskAndTeam.objects.filter(task=obj)])):
            dt={
                "title":"New task assign {} to you".format(obj.title),
                "description":"Task assign",
                "type":"response",
                "created_for":judge,
                "req_data":{}
            }
            create_notification(dt,request)
        return Response({"msg":"judges assigned randomly to this task","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=["post"],url_path="lock")
    def task_lock(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        obj = self.get_object()
        lock = TaskLock.objects.filter(task=obj)
        if lock:
            lock = lock[0]
            if lock.lock:
                return Response({"msg":"Already Lock","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

        lock = TaskLock.objects.create(task=obj)
        lock.lock = True
        lock.save()
        obj.is_randomized = True
        obj.save()
        return Response({"msg":"judges locked successfully.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)



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

        # if datetime.datetime().now() > datetime.datetime.strptime(obj.task.submission_due_date, '%Y-%m-%d, %I:%M:%S %p'):
        #     return Response({"msg":"You can't submit a task after submission due date has been passed.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

        for key,value in request.data.items():
            setattr(obj,key,value)

        if request.FILES.getlist("doc",None):
            ParticipantTaskdocs.objects.filter(task=obj).delete()

            for d in request.FILES.getlist("doc"):
                ParticipantTaskdocs.objects.create(doc=d,task=obj,submitted_date=request.data.get("submitted_date",None))

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

    @action(detail=True, methods=["get"], url_path="individual-tasks")
    def get_individual_task(self,request,*args,**kwargs):
        if not (request.user.is_superuser or request.user.is_judge):
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        task = Task.objects.filter(id=kwargs.get("pk"))
        if not task:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)

        task = task[0]
        judges = [task.judge for task in AssingJudgeToTask.objects.filter(task=task,task__assing_to="individuals").order_by("id")]
        participants = ParticipantTask.objects.filter(task=task,task__assing_to="individuals")

        if request.query_params.get("pname",None):
            participants=participants.filter(participant__user__full_name__icontains=request.query_params.get("pname"))
        count=len(participants)
        participants = participants[int(request.query_params.get("offset",0) or 0):int(request.query_params.get("limit",10) or 10)+int(request.query_params.get("offset",0) or 0)]
        serializer = self.get_serializer(participants, many=True,context={"request":request})

        return Response({"data":{
            "individuals":serializer.data,
            "judges":UserSerializer(judges,context={"request":request},many=True).data},
            "count":count,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="list-all-participant")
    def all_participant_and_teams(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        obj = Task.objects.filter(id=kwargs.get("pk")).first()
        if not obj:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        task_info = TaskDetailsSerializer(obj).data

        # Already Graded Participant
        participants = ParticipantTask.objects.filter(task=obj, task__assing_to="individuals", participant__user__is_participant=True)

        if request.query_params.get("pname", None):
            participants=participants.filter(participant__user__full_name__icontains=request.query_params.get("pname"))
        count=len(participants)

        serializer = self.get_serializer(participants, many=True,context={"request":request})
        data = serializer.data

        judges=[ task.judge for task in AssingJudgeToTask.objects.filter(task=obj)]

        resp = {
            "data":{
                "individuals":data,
                "count":count,
                "judges":UserSerializer(judges,many=True).data
                },
            "status":status.HTTP_200_OK
            }
        return Response(resp,status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="list-all-teams")
    def list_all_teams(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

        obj = Task.objects.filter(id=kwargs.get("pk")).first()
        if not obj:
            return Response({"msg":"No task found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        # task_info = TaskDetailsSerializer(obj).data

        # TEAM Participants
        team_participants = Team.objects.filter()#.exclude(team__id__isnull=True) #task=obj, task__assing_to="teams"


        if request.query_params.get("pname", None):
            team_participants=team_participants.filter(participant__user__full_name__icontains=request.query_params.get("pname"))

        track = request.query_params.get("track", None)
        if track is not None and len(track)>0:
            track = int(track)
            team_participants=team_participants.filter(team_track=track)

        team_count=len(team_participants)

        serializer = TeamSerializerTaskDetails(team_participants, many=True,context={"request":request, "task":obj})
        data = serializer.data


        judges=[ task.judge for task in AssingJudgeToTask.objects.filter(task=obj)]

        resp = {
            "data":{
                "teams":data,
                "count":team_count,
                "judges":UserSerializer(judges,many=True).data
                },
            "status":status.HTTP_200_OK
            }
        return Response(resp,status=status.HTTP_200_OK)


    @action(detail=False,methods=["get"],url_path="live-judge-task")
    def live_judge_task_listing(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        rjdt = RandomJudgeToTaskAndTeam.objects.filter(judge=request.user).exclude(task__event__id__isnull=True).order_by("-id")
        task_list2 = AssingJudgeToTask.objects.filter(judge=request.user).exclude(task__event__id__isnull=True).order_by("id")

        task_list = []
        for task in rjdt:
            task_list.append(task.task)
        try:
            for task_2 in task_list2:
                for _task in task_2.task.all():
                    task_list.append(_task)
        except:
            pass
        task_list=list(set(task_list))
        count=len(task_list)

        # TODO Change Pageing to dblevl Not after pulling all records
        if request.query_params.get("limit",'10') and request.query_params.get("offset","0"):
            task_list = task_list[int(request.query_params.get("offset",'0')):int(request.query_params.get("limit","0"))+int(request.query_params.get("offset",'0'))]

        return Response({"data":TaskSerializers(task_list,many=True,context={"request":request}).data,"count":count,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)


    @action(detail=False,methods=["get"],url_path="judge-task")
    def judge_task_listing(self,request,*args,**kwargs):
        if not request.user.is_judge:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        rjdt = RandomJudgeToTaskAndTeam.objects.filter(judge=request.user, task__event__id__isnull=True).order_by("-id")
        task_list2 = AssingJudgeToTask.objects.filter(judge=request.user, task__event__id__isnull=True).order_by("id")

        task_list = []
        for task in rjdt:
            task_list.append(task.task)
        try:
            for task_2 in task_list2:
                for _task in task_2.task.all():
                    task_list.append(_task)
        except:
            pass
        task_list=list(set(task_list))
        count=len(task_list)

        # TODO Change Pageing to dblevl Not after pulling all records
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
            tasks = []
            rjdt = RandomJudgeToTaskAndTeam.objects.filter(judge=request.user).order_by("-id")
            for task in rjdt:
                tasks.append(task.task)

            judge_task_list = AssingJudgeToTask.objects.filter(judge=request.user).order_by("id")
            task_list= []
            for judge_task in judge_task_list:
                for _task in judge_task.task.all():
                    tasks.append(_task)

            judge_tasks = Task.objects.filter(id__in=[task.id for task in tasks]).distinct().order_by("-id")
            queryset = self.filter_queryset(judge_tasks)
            page = self.paginate_queryset(queryset)
            ts=[]
            if page is not None:
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



