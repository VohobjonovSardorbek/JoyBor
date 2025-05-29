from django_filters import rest_framework as filters
from .models import Student

class StudentFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    floor_id = filters.NumberFilter(field_name='floor_id')

    class Meta:
        model = Student
        fields = ['name', 'last_name', 'floor_id']