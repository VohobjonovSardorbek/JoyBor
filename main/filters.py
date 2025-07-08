from django_filters import rest_framework as filters
from .models import Student, Application, Task

class StudentFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    floor_id = filters.NumberFilter(field_name='floor_id')
    status = filters.ChoiceFilter(
        field_name='status',
        choices=Student.STATUS_CHOICES,
        label='Status'
    )
    class Meta:
        model = Student
        fields = ['name', 'last_name', 'floor_id', 'status']



class ApplicationFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        field_name='status',
        choices=Application.STATUS_CHOICES,
        label='Status'
    )

    class Meta:
        model = Application
        fields = ['status']


class TaskFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Task.STATUS_CHOICES)

    class Meta:
        model = Task
        fields = ['status']


