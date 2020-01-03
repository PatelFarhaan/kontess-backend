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

from app.models.user import User,UserSkills,ManageRegistration
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from app.models.team import Invitation
from app.models.judge import TeamMentorRequest
from app.models.participant import Participant
from bson.json_util import default


class UserSkillSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserSkills
        fields = ("id","label","value")
        read_only_fields=("value",)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField()
    role = serializers.CharField()
    user_image = serializers.SerializerMethodField()
    skill = UserSkillSerializer(many = True,allow_null=True,required=False)
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data["full_name"]
        )
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'full_name',"user_image", 'role','biography',"created_on",'skill')
        read_only_fields = ('id','user_image',"created_on","skill")

    def get_user_image(self,obj):
        if obj.user_image:
            request=self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.user_image.url)
            return None
        
    def to_representation(self, instance):
        request = self.context.get("request",None)
        team_id = self.context.get("team_id",None)
        if not team_id:
            return super().to_representation(instance)
        data = super().to_representation(instance)
        invites = Invitation.objects.filter(team_id = team_id, participants__in = Participant.objects.filter(user=instance))
        data["status"] = invites[0].status if invites else None
        mentor_request = TeamMentorRequest.objects.filter(team_id=team_id,for_judge=instance)
        if mentor_request:
            mentor_request=mentor_request[0]
            if mentor_request.admin_status != "rejected" and mentor_request.judge_status != "rejected":
                data["judge_status"] = mentor_request.judge_status if mentor_request else None
                data["admin_status"] = mentor_request.admin_status if mentor_request else None
        return data
    
class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(min_length=8)

    class Meta:
        model = User
        fields = ('username', 'password')


class UserIdSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField()

    class Meta:
        model = User
        fields = ['user_id']


class ManageRegistrationSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = ManageRegistration
        fields = ("id","judge_count","participant_count","reg_date","status","created_by","created_on")
        read_only_fields= ("created_on",)

