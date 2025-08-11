from django.db.models import Sum
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
    placement_status = filters.ChoiceFilter(
        field_name='placement_status',
        choices=Student.PLACEMENT_STATUS_CHOICES,
        label='Joylashish holati'
    )
    max_payment = filters.NumberFilter(
        method='filter_max_payment',
        label="To‘lov summasi (kamroq)"
    )

    class Meta:
        model = Student
        fields = ['name', 'last_name', 'floor_id', 'status', 'placement_status', 'max_payment']

    def filter_max_payment(self, queryset, name, value):
        # To‘lovlarni summalab, umumiy to‘lov summasi value dan kamroq bo‘lganlarni chiqaramiz
        queryset = queryset.annotate(total_paid=Sum('payments__amount'))
        return queryset.filter(total_paid__lt=value)


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


