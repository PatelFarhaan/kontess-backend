from django_filters.rest_framework import Filter,FilterSet
from django_filters import filters
from rest_framework import viewsets
from app.models.team import Team,TeamDocs

class TeamFilter(FilterSet):
    name = filters.CharFilter(field_name = 'name',lookup_expr='icontains')
    sort_by = filters.OrderingFilter(choices=(
            ('created_on', 'Created on asc'),
            ('-created_on', 'Created on desc'),
            ("name","A-Z"),
            ("-name","Z-A")
        ),
        fields={
            'created_on': 'created_on',
            'name':"name"
        },
    )
    class Meta:
        model = Team
        fields=["name","sort_by"]



class TeamDocsFilter(FilterSet):
    sort_by = filters.OrderingFilter(choices=(
            ('created_on', 'Created on asc'),
            ('-created_on', 'Created on desc'),
        ),
        fields={
            'created_on': 'created_on',
        }
    )
    class Meta:
        model = TeamDocs
        fields=["sort_by"]
