

from rest_framework import serializers
from app.models.judge import Judge,JudgeRequest,TeamMentorRequest,JudgeRequestTeam
from app.serializers.team import TeamSerializer
from app.serializers.user import UserSerializer

class JudgeSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Judge
        fields = ('id', 'user')

    def get_user(self, obj):
        return UserSerializer(obj.user,context={"request":self.context.get("request")}).data

class JudgeRequestSerializer(serializers.ModelSerializer):
    judge = JudgeSerializer(allow_null=True,required=False)
    created_for = serializers.SerializerMethodField()
    class Meta:
        model = JudgeRequest
        fields = "__all__"
    
    def get_created_for(self, obj):
        return UserSerializer(obj.created_for,context={"request":self.context.get("request")}).data


class TeamMentorRequestSerializer(serializers.ModelSerializer):
    team = TeamSerializer(allow_null=True,required=False)
    for_judge = UserSerializer(allow_null=True,required=False)
    for_admin = UserSerializer(allow_null=True,required=False)

    class Meta:
        model = TeamMentorRequest
        fields = "__all__"

class JudgeRequestTeamSerializer(serializers.ModelSerializer):
    created_for = UserSerializer(allow_null=True,required=False)
    judge = JudgeSerializer(allow_null=True,required=False)
    
    class Meta:
        model = JudgeRequestTeam
        fields = "__all__"