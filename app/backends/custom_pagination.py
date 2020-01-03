from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework import status
class MyCustomPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response({
            'status':status.HTTP_200_OK,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.count,
            'data': data
        })