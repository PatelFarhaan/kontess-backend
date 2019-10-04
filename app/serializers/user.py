from app.models.user import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(min_length=8)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_judge = serializers.BooleanField()
    is_participant = serializers.BooleanField()
    is_organizer = serializers.BooleanField()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"]
        )
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name','is_judge','is_participant','is_organizer')