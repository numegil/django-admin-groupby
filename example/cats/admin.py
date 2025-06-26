from django.contrib import admin
from django.db.models import Count, Sum, Avg, Min, Max, StdDev, Variance, Case, When
from .models import Cat
from django_admin_groupby.admin import GroupByAdminMixin
from django_admin_groupby.aggregations import PostProcess

@admin.register(Cat)
class CatAdmin(GroupByAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'age', 'weight', 'color', 'breed', 'is_vaccinated')
    list_filter = ('is_vaccinated', 'color', 'breed')
    search_fields = ('name',)
    
    group_by_fields = ['color', 'breed', 'is_vaccinated', 'adoption_date__year', 'adoption_date__month', 'adoption_date__quarter', 'adoption_date__weekday']
    group_by_aggregates = {
        'id': {
            'count': Count('id', extra={'verbose_name': "Count"}),
            'senior_cats': Count(Case(When(age__gt=10, then=1)), extra={'verbose_name': "Senior Cats"}),
        },
        'breed': {
            'distinct_count': Count('breed', distinct=True, extra={'verbose_name': "Unique Breeds"}),
        },
        'weight': {
            'avg': Avg('weight', extra={'verbose_name': "Average Weight"}),
            'sum': Sum('weight', extra={'verbose_name': "Total Weight"}),
            # 'stddev': StdDev('weight', extra={'verbose_name': "Weight Variation"}),
            # 'max': Max('weight', extra={'verbose_name': "Maximum Weight"}),
            # 'min': Min('weight', extra={'verbose_name': "Minimum Weight"})
        },
        'age': {
            'avg': Avg('age', extra={'verbose_name': "Average Age"}),
            # 'variance': Variance('age', extra={'verbose_name': "Age Variance"}),
            # 'max': Max('age', extra={'verbose_name': "Maximum Age"})
        },
        'name_length': {
            'total': PostProcess(
                lambda cat: len(cat.name),
                verbose_name='Total Name Length', 
                aggregate='sum'
            )
        }
    }