from rest_framework import serializers
from rest_framework.validators import UniqueValidator


from app.models.team import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=Team.objects.all())]
    )
    description = serializers.CharField(max_length=100)
    requests = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    def create(self, validated_data):
        team = Team.objects.create(
            name=validated_data['name'], 
            description=validated_data['description']
        )
        return team

    class Meta:
        model = Team
        fields = ('id', 'name','description', 'requests', 'participants')
