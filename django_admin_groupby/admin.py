from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class GroupByFilter(SimpleListFilter):
    title = _('Group by')
    parameter_name = 'groupby'
    template = 'admin/group_by_filter.html'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.model_admin = model_admin
        self.used_parameters = {}
        
        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            if value:
                self.used_parameters[self.parameter_name] = value

    def lookups(self, request, model_admin):
        group_by_fields = getattr(model_admin, 'group_by_fields', [])
        return [(field, field.replace('_', ' ').title()) 
                for field in group_by_fields]

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        current_values = []
        if self.parameter_name in changelist.params:
            current_values = changelist.params[self.parameter_name].split(',')
        
        yield {
            'selected': not current_values,
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
            'display': _('All'),
        }
        
        for lookup, title in self.lookup_choices:
            is_selected = lookup in current_values
            
            if is_selected:
                new_values = [v for v in current_values if v != lookup]
                query_string = changelist.get_query_string({
                    self.parameter_name: ','.join(new_values) if new_values else None
                })
            else:
                new_values = current_values + [lookup]
                query_string = changelist.get_query_string({
                    self.parameter_name: ','.join(new_values)
                })
            
            yield {
                'selected': is_selected,
                'query_string': query_string,
                'display': title,
            }
    
    def queryset(self, request, queryset):
        """
        Return the filtered queryset.
        
        This is required by Django's ListFilter interface even though 
        our filtering happens in GroupByAdminMixin.changelist_view.
        """
        return queryset


class GroupByAdminMixin:
    group_by_fields = []
    group_by_aggregates = {
        'id': {'count': Count('id', extra={'verbose_name': "Count"})}
    }
    
    change_list_template = 'admin/grouped_change_list.html'

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if self.group_by_fields:
            return list(list_filter) + [GroupByFilter]
        return list_filter

    def changelist_view(self, request, extra_context=None):
        groupby_param = request.GET.get('groupby', '')
        if not groupby_param:
            return super().changelist_view(request, extra_context)
            
        groupby_fields = groupby_param.split(',')
        
        for field in groupby_fields:
            if field not in self.group_by_fields:
                return super().changelist_view(request, extra_context)

        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)
        
        flat_aggregates = {}
        for field, operations in self.group_by_aggregates.items():
            for op_name, op_func in operations.items():
                flat_aggregates[f"{field}__{op_name}"] = op_func
        
        grouped_qs = queryset.values(*groupby_fields).annotate(**flat_aggregates).order_by(*groupby_fields)
        
        totals = {}
        for field, operations in self.group_by_aggregates.items():
            for op_name in operations.keys():
                agg_key = f"{field}__{op_name}"
                try:
                    if op_name == 'avg':
                        # Find a count field to use for weighted average
                        count_key = next((f"{count_field}__{count_op}" for count_field, count_ops in self.group_by_aggregates.items() 
                                         for count_op in count_ops if count_op == 'count'), None)
                        
                        # Handle empty queryset case first
                        if not grouped_qs:
                            totals[agg_key] = 0
                        # Use weighted average when count field exists
                        elif count_key:
                            weighted_sum = sum(item[agg_key] * item[count_key] for item in grouped_qs)
                            total_count = sum(item[count_key] for item in grouped_qs)
                            totals[agg_key] = weighted_sum / total_count if total_count > 0 else 0
                        # Fall back to simple average
                        else:
                            totals[agg_key] = sum(item[agg_key] for item in grouped_qs) / len(grouped_qs)
                    else:
                        totals[agg_key] = sum(item[agg_key] for item in grouped_qs)
                except (TypeError, ValueError):
                    totals[agg_key] = None
        
        groupby_field_names = []
        fields_with_choices = []
        
        for field_name in groupby_fields:
            field_obj = self.model._meta.get_field(field_name)
            
            # Track fields that have choices
            if hasattr(field_obj, 'choices') and field_obj.choices:
                fields_with_choices.append(field_name)
            
            # Get the display name for column headers
            if hasattr(field_obj, 'verbose_name') and field_obj.verbose_name:
                verbose_name = str(field_obj.verbose_name)
                groupby_field_names.append(verbose_name)
            else:
                title = field_name.replace('_', ' ').title()
                groupby_field_names.append(title)
        
        aggregate_info = []
        for field, operations in self.group_by_aggregates.items():
            for op_name in operations.keys():
                agg_func = operations[op_name]
                verbose_name = None
                
                if hasattr(agg_func, 'extra') and isinstance(agg_func.extra, dict):
                    # Try to get verbose_name directly from extra dict
                    verbose_name = agg_func.extra.get('verbose_name')
                    
                    # If not found, check nested extra dict
                    if not verbose_name and 'extra' in agg_func.extra and isinstance(agg_func.extra['extra'], dict):
                        verbose_name = agg_func.extra['extra'].get('verbose_name')
                
                if verbose_name:
                    label = str(verbose_name)
                else:
                    if field == 'id' and op_name == 'count':
                        label = "Count"
                    else:
                        label = f"{op_name.capitalize()} {field.replace('_', ' ')}"
                
                aggregate_info.append({
                    'key': f"{field}__{op_name}",
                    'field': field,
                    'operation': op_name,
                    'label': label
                })
        
        class ChangeListTotals:
            def __init__(self, original_cl, **kwargs):
                for attr in dir(original_cl):
                    if not attr.startswith('__') and not callable(getattr(original_cl, attr)):
                        setattr(self, attr, getattr(original_cl, attr))
                
                for key, value in kwargs.items():
                    setattr(self, key, value)
                
                if not hasattr(self, 'formset'):
                    self.formset = None
                if not hasattr(self, 'result_hidden_fields'):
                    self.result_hidden_fields = []
                
                self.get_query_string = original_cl.get_query_string
                    
        cl_totals = ChangeListTotals(
            cl,
            grouped_results=grouped_qs,
            groupby_fields=groupby_fields,
            groupby_field_names=groupby_field_names,
            fields_with_choices=fields_with_choices,
            aggregate_info=aggregate_info,
            totals=totals
        )
        
        context = {
            **self.admin_site.each_context(request),
            'cl': cl_totals,
            'grouped_results': grouped_qs,
            'groupby_fields': groupby_fields,
            'groupby_field_names': groupby_field_names,
            'fields_with_choices': fields_with_choices,
            'aggregate_info': aggregate_info,
            'totals': totals,
            'title': cl.title,
            'is_popup': cl.is_popup,
            'model_admin': self,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return TemplateResponse(request, self.change_list_template, context)