from django_filters.rest_framework import Filter,FilterSet
from django_filters import filters
from rest_framework import viewsets
from app.models.judge import JudgeRequest

class JudgeRequestFilter(FilterSet):
    status = filters.CharFilter(field_name = 'status',lookup_expr='exact')
    sorting = filters.OrderingFilter(choices=(
            ('created_on', 'Created on asc'),
            ('-created_on', 'Created on desc'),
        ),
        fields={
            'created_on': 'created_on',
            'status':"status"
        },
    )
    class Meta:
        model = JudgeRequest
        fields=["status","sorting"]



