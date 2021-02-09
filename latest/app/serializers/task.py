from rest_framework import serializers
from django.db.models import Q,Count

import json
from app.models.task import Task, QuestionsCriteria,ParticipantTask,AssingJudgeToTask,ParticipantTaskdocs,TaskGrading,TaskGrades,TaskLock,RandomJudgeToTaskAndTeam
from app.serializers.user import UserSerializer
from app.serializers.team import TeamTrackSerializer,TeamSerializer
from app.serializers.participant import ParticipantDetailSerializer



class TaskGradeSerializers(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    class Meta:
        model = TaskGrades
        fields= ("id","questions","score","created_on","comment")
    def get_questions(self,obj):
        return QuestionsCriteriaSerializers(obj.questions).data if obj.questions else {}

class TaskGradingSerializers(serializers.ModelSerializer):
    team = TeamSerializer(allow_null=True,required=False)
    participant = ParticipantDetailSerializer(allow_null=True,required=False)
    judge = UserSerializer(allow_null=True,required=False)
    grades = TaskGradeSerializers(many=True,allow_null=True,required=False)
    class Meta:
        model = TaskGrading
        fields= ("id","team","participant","task","judge","grades","over_all_comments","status")


class QuestionsCriteriaSerializers(serializers.ModelSerializer):
    class Meta:
        model = QuestionsCriteria
        fields= ("id","question","max_score","feedback", "track")


class TaskSerializers(serializers.ModelSerializer):
    created_by = UserSerializer(allow_null=True,required=False)
    questions = QuestionsCriteriaSerializers(allow_null=True,required=False,many=True)
    task_grading = TaskGradingSerializers(many=True,allow_null=True,required=False)
    class Meta:
        model = Task
        fields= ("id","title","description","submission_due_date","grade_due_date","max_no_of_judge","created_on","created_by",
                 "questions","assing_to","status","task_grading","release_score_to_participant","is_randomized", "event")

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         try:
#             lock = TaskLock.objects.get(task=instance).values("lock")
#             data["is_judge_locked"] = lock.get("lock")
#         except Exception as e:
#             print(e)
#             pass
#         return data




class ParticipantTaskdocSerializer(serializers.ModelSerializer):
    doc = serializers.FileField()
    class Meta:
        model = ParticipantTaskdocs
        fields = '__all__'

class ParticipantTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializers(allow_null=True,required=False)
    team = TeamSerializer(allow_null=True,required=False)
    participant = ParticipantDetailSerializer(allow_null=True,required=False)
    submitted_docs = ParticipantTaskdocSerializer(many=True,required=False,allow_null=True)
    submitted_by = UserSerializer(allow_null=True,required=False)
    task_grading = TaskGradingSerializers(many=True,allow_null=True,required=False)

    class Meta:
        model = ParticipantTask
        fields= "__all__"
        read_only_fields= ("id","task","submitted_docs","submitted_by","task_grading")

    def to_representation(self, instance):
        request = self.context.get("request")
        data = super().to_representation(instance)
        if request.user.is_judge:
            task_grading = TaskGradingSerializers(TaskGrading.objects.filter(grade=instance,judge=request.user),many=True,context={"request":request}).data
        return data

class AssingJudgeToTaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(allow_null=True,required=False)
    task = TaskSerializers(allow_null=True,required=False)
    judge = UserSerializer(allow_null=True,required=False)
    track = TeamTrackSerializer(allow_null=True,required=False)

    class Meta:
        model = AssingJudgeToTask
        fields= "__all__"
        read_only_fields= ("id","task","created_by")


class AssingJudgeToTaskDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(allow_null=True,required=False)
    task = TaskSerializers(many=True,allow_null=True,required=False)
    judge = UserSerializer(allow_null=True,required=False)
    track = TeamTrackSerializer(many=True,allow_null=True,required=False)

    class Meta:
        model = AssingJudgeToTask
        fields= "__all__"

class ParticipantTaskDetailsSerializer(serializers.ModelSerializer):
    team = TeamSerializer(allow_null=True,required=False)
    participant = ParticipantDetailSerializer(allow_null=True,required=False)
    submitted_docs = ParticipantTaskdocSerializer(many=True,required=False,allow_null=True)
    submitted_by = UserSerializer(allow_null=True,required=False)
    task_grading = TaskGradingSerializers(many=True,allow_null=True,required=False)

    class Meta:
        model = ParticipantTask
        fields= "__all__"
        read_only_fields= ("id","submitted_docs","submitted_by","task_grading")



class TaskDetailsSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(allow_null=True,required=False)
    questions = QuestionsCriteriaSerializers(allow_null=True,required=False,many=True)

    class Meta:
        model = Task
        fields= ("id","title","description", "submission_due_date","grade_due_date","max_no_of_judge",
                 "created_on","created_by","questions","assing_to","status","is_randomized")

    def to_representation(self, instance):
        request = self.context.get("request")
        data = super().to_representation(instance)
        ptasks = ParticipantTask.objects.filter(task=instance)
        stcounts = ptasks.values("status").annotate(status_count = Count("status"))
        data["task_submission_counts"]={"total_task":ptasks.count()}
        for count in stcounts:
            data["task_submission_counts"].update({count.get("status"):count.get("status_count",0)})

        if not data["task_submission_counts"].get("submit",None):
               data["task_submission_counts"]["submit"] = 0

        if not data["task_submission_counts"].get("pending",None):
               data["task_submission_counts"]["pending"] = 0

        ajtks = AssingJudgeToTask.objects.filter(task=instance)
        judges = []
        grading_count=0
        for ajtk in ajtks:
            if ajtk.judge:
                judges.append(ajtk.judge)
                if len(ptasks) == TaskGrading.objects.filter(task=instance,judge=ajtk.judge).count():
                    grading_count = grading_count + 1

        data["task_grading_counts"] = {
                "total_no_of_juges":len(judges),
                "judge_graded": grading_count,
            }

        lock = TaskLock.objects.filter(task=instance)
        if lock:
            lock = lock[0]
            data["is_judge_locked"] = lock.lock
        return data

