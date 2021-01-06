from django_filters.rest_framework import Filter,FilterSet
from django_filters import filters
from rest_framework import viewsets
from app.models.task import Task

class TaskFilter(FilterSet):
    title = filters.CharFilter(field_name = 'title',lookup_expr='icontains')
    sort_by = filters.OrderingFilter(choices=(
            ('created_on', 'Created on asc'),
            ('-created_on', 'Created on desc'),
            ("title","A-Z"),
            ("-title","Z-A"),
            ("submission_due_date","Submision Date asc"),
            ("-submission_due_date","Submision Date desc"),
            ("grade_due_date","Grading Date asc"),
            ("-grade_due_date","Grading Date desc")
        ),
        fields={
            'created_on': 'created_on',
            'title':"title"
        },
    )
    class Meta:
        model = Task
        fields=["title","sort_by"]




