from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

class MyCustomPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response({
            'status':200,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.count,
            'data': data
        })