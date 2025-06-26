from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Count, Value
from django.db.models.functions import Extract, Concat
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from django_admin_groupby.aggregations import PostProcess


class GroupByFilter(SimpleListFilter):
    title = _('Group by')
    parameter_name = 'groupby'
    template = 'admin/group_by_filter.html'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.model_admin = model_admin
        
        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            if value:
                self.used_parameters = {self.parameter_name: value}

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
    
    def _is_post_process_field(self, field_name):
        """Check if a field is a post-processed field."""
        clean_name = field_name[1:] if field_name.startswith('-') else field_name
        
        for field, operations in self.group_by_aggregates.items():
            for op_name, op_func in operations.items():
                if clean_name == f"{field}__{op_name}" and isinstance(op_func, PostProcess):
                    return True
        return False
    
    def _parse_date_field(self, field_spec):
        """Parse field__year syntax and return (field_name, date_part) or (field_spec, None)."""
        if '__' in field_spec:
            parts = field_spec.split('__')
            if len(parts) == 2:
                date_parts = ['year', 'month', 'day', 'week', 'quarter', 'iso_week', 'weekday', 'hour']
                if parts[1] in date_parts:
                    return parts[0], parts[1]
        return field_spec, None
    
    def _build_date_annotation(self, field_name, date_part):
        """Build Django annotation for extracting date part."""
        if date_part == 'month':
            # Month should include year for meaningful grouping
            from django.db.models import CharField
            from django.db.models.functions import Cast
            return Concat(
                Cast(Extract(field_name, 'year'), output_field=CharField()),
                Value('-'),
                Cast(Extract(field_name, 'month'), output_field=CharField())
            )
        elif date_part == 'iso_week':
            return Extract(field_name, 'week')
        elif date_part == 'weekday':
            return Extract(field_name, 'week_day')
        else:
            return Extract(field_name, date_part)
    
    def _format_date_value(self, value, date_part):
        """Format date values for display."""
        if value is None:
            return None
            
        if date_part == 'month':
            # Format as "YYYY-MM" to "Month YYYY"
            parts = str(value).split('-')
            if len(parts) == 2:
                import calendar
                year = parts[0]
                month = int(parts[1])
                return f"{calendar.month_name[month]} {year}"
            return str(value)
        elif date_part == 'quarter':
            return f"Q{value}"
        elif date_part == 'week':
            return f"Week {value}"
        elif date_part == 'day':
            return f"Day {value}"
        elif date_part == 'weekday':
            # Convert weekday number to name (1=Sunday, 7=Saturday in Django)
            weekdays = ['', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            return weekdays[int(value)]
        elif date_part == 'hour':
            return f"{value}:00"
        else:
            # Year or other parts
            return str(value)
        
    def get_filter_url_for_group(self, cl, group_values, groupby_fields):
        filter_params = {}
        
        for field_spec in groupby_fields:
            # Parse date field if needed
            field_name, date_part = self._parse_date_field(field_spec)
            
            # Get the actual value from the group_values
            if date_part:
                value_key = f"{field_name}__{date_part}"
                value = group_values.get(value_key)
            else:
                value = group_values.get(field_spec)
            
            field_obj = self.model._meta.get_field(field_name)
            
            # Handle date fields with extraction
            if date_part and value is not None:
                if date_part == 'month':
                    # Split year-month value and create separate filters
                    parts = str(value).split('-')
                    if len(parts) == 2:
                        filter_params[f"{field_name}__year"] = parts[0]
                        filter_params[f"{field_name}__month"] = parts[1]
                else:
                    filter_params[f"{field_name}__{date_part}"] = value
                    
                    # For day/week filtering, also include the year if available
                    if date_part in ['day', 'week']:
                        # Check if we have year data in the group
                        year_field = f"{field_name}__year"
                        if year_field in groupby_fields:
                            year_value = group_values.get(f"{field_name}__year")
                            if year_value:
                                filter_params[f"{field_name}__year"] = year_value
            # Handle boolean fields
            elif field_obj.get_internal_type() == 'BooleanField':
                if value is None:
                    filter_params[f"{field_name}__isnull"] = 'True'
                else:
                    value = '1' if value else '0'
                    filter_params[f"{field_name}__exact"] = value
            # Handle choice fields
            elif hasattr(field_obj, 'choices') and field_obj.choices:
                filter_params[f"{field_name}__exact"] = value
            else:
                filter_params[field_name] = value
            
        return cl.get_query_string(filter_params, remove=['groupby', 'sort'])
    
    def _apply_aggregation(self, values, agg_type):
        """Apply aggregation of the specified type to a list of values."""
        if not values:
            return 0
            
        if agg_type == 'avg':
            return sum(values) / len(values)
        elif agg_type == 'sum':
            return sum(values)
        elif agg_type == 'min':
            return min(values)
        elif agg_type == 'max':
            return max(values)
        elif agg_type == 'count':
            return len(values)
        # Default to sum for unknown aggregation types
        return sum(values)

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if self.group_by_fields:
            return [GroupByFilter] + list(list_filter)
        return list_filter

    def get_changelist_instance(self, request):
        """Override to ensure date filters show 'Clear all filters' link."""
        cl = super().get_changelist_instance(request)
        
        # Check if we have date filter parameters
        date_parts = ['year', 'month', 'day', 'week', 'quarter', 'iso_week', 'weekday', 'hour']
        date_filter_params = [
            param for param in request.GET 
            if '__' in param and param.split('__')[1] in date_parts
            and param not in ['groupby', 'sort', 'o', 'p', 'q']
        ]
        
        # If we have date filters, ensure the filters UI shows up
        if date_filter_params:
            # Need to have at least one filter spec for has_filters to be True
            if cl.filter_specs:
                cl.has_filters = True
                cl.has_active_filters = True
                
                # Rebuild clear_all_filters_qs to include our date filter params
                params_to_remove = list(cl.get_filters_params().keys()) + date_filter_params
                cl.clear_all_filters_qs = cl.get_query_string(remove=params_to_remove)
        
        return cl
    
    def changelist_view(self, request, extra_context=None):
        groupby_param = request.GET.get('groupby', '')
        if not groupby_param:
            return super().changelist_view(request, extra_context)
            
        groupby_fields = groupby_param.split(',')
        
        for field in groupby_fields:
            if field not in self.group_by_fields:
                return super().changelist_view(request, extra_context)
        
        request_copy = request.GET.copy()
        sort_param = request_copy.pop('sort', [''])[0]
        request.GET = request_copy
        
        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)
        
        # Process date fields and build annotations
        date_annotations = {}
        values_fields = []
        
        for field_spec in groupby_fields:
            field_name, date_part = self._parse_date_field(field_spec)
            if date_part:
                # This is a date field with extraction
                annotation_name = f"{field_name}__{date_part}"
                date_annotations[annotation_name] = self._build_date_annotation(field_name, date_part)
                values_fields.append(annotation_name)
            else:
                # Regular field
                values_fields.append(field_spec)
        
        # Apply date annotations to queryset
        if date_annotations:
            queryset = queryset.annotate(**date_annotations)
        
        flat_aggregates = {}
        post_process_aggregates = {}
        
        for field, operations in self.group_by_aggregates.items():
            for op_name, op_func in operations.items():
                if isinstance(op_func, PostProcess):
                    post_process_aggregates[(field, op_name)] = op_func
                else:
                    flat_aggregates[f"{field}__{op_name}"] = op_func
        
        sort_order = []
        sort_field = None
        sort_direction = ''
        original_sort_param = sort_param
        
        is_post_process_sort = False
        post_process_sort_field = None
        
        if sort_param:
            desc = False
            if sort_param.startswith('-'):
                desc = True
                sort_param = sort_param[1:]
            
            # Check if sorting by a groupby field
            if sort_param in groupby_fields:
                sort_field = sort_param
                sort_direction = 'descending' if desc else 'ascending'
                sort_order = [f"{'-' if desc else ''}{sort_param}"]
            else:
                # Check if sorting by an aggregate field
                for field, operations in self.group_by_aggregates.items():
                    for op_name in operations.keys():
                        agg_key = f"{field}__{op_name}"
                        if sort_param == agg_key:
                            sort_field = agg_key
                            sort_direction = 'descending' if desc else 'ascending'
                            
                            if op_name != 'post_process':
                                sort_order = [f"{'-' if desc else ''}{agg_key}"]
                            else:
                                is_post_process_sort = True
                                post_process_sort_field = agg_key
                                sort_order = groupby_fields.copy()
                            break
        
        if not sort_order:
            sort_order = groupby_fields.copy()
            
        # Check if we're trying to sort by a post-processed field
        is_post_process_sort = any(self._is_post_process_field(param) for param in sort_order)
                
        if is_post_process_sort:
            # For post-process sorting, don't include it in the database query
            grouped_qs = queryset.values(*values_fields).annotate(**flat_aggregates).order_by(*values_fields)
        else:
            # For regular sorting, use the provided sort order
            grouped_qs = queryset.values(*values_fields).annotate(**flat_aggregates).order_by(*sort_order)
        
        result_objects = None
        if post_process_aggregates:
            result_objects = {}
            for group_values in grouped_qs:
                filter_kwargs = {}
                for field_spec in groupby_fields:
                    field_name, date_part = self._parse_date_field(field_spec)
                    if date_part:
                        # Use the annotated field name for date fields
                        annotation_name = f"{field_name}__{date_part}"
                        filter_kwargs[f"{field_name}__{date_part}"] = group_values[annotation_name]
                    else:
                        filter_kwargs[field_spec] = group_values[field_spec]
                group_objects = list(queryset.filter(**filter_kwargs))
                group_key = tuple(group_values[field] for field in values_fields)
                result_objects[group_key] = group_objects
        
        for group_dict in grouped_qs:
            if post_process_aggregates:
                group_key = tuple(group_dict[field] for field in values_fields)
                group_objects = result_objects.get(group_key, [])
                for (field, op_name), pp_obj in post_process_aggregates.items():
                    agg_key = f"{field}__{op_name}"
                    values = [pp_obj.func(obj) for obj in group_objects]
                    group_dict[agg_key] = self._apply_aggregation(values, pp_obj.aggregate)
            
            # Add formatted versions of date fields
            for field_spec in groupby_fields:
                field_name, date_part = self._parse_date_field(field_spec)
                if date_part:
                    annotation_name = f"{field_name}__{date_part}"
                    raw_value = group_dict.get(annotation_name)
                    formatted_value = self._format_date_value(raw_value, date_part)
                    group_dict[f"{annotation_name}_display"] = formatted_value
            
            group_dict['_filter_url'] = self.get_filter_url_for_group(cl, group_dict, groupby_fields)
        
        if is_post_process_sort:
            post_process_sort_params = []
            for param in sort_order:
                if self._is_post_process_field(param):
                    clean_param = param[1:] if param.startswith('-') else param
                    desc = param.startswith('-')
                    post_process_sort_params.append((clean_param, desc))
            
            grouped_qs = list(grouped_qs)
            
            # Sort by all post-processed fields that were requested
            for sort_param, is_desc in reversed(post_process_sort_params):
                grouped_qs.sort(
                    key=lambda x: (x.get(sort_param) is None, x.get(sort_param, 0)),
                    reverse=is_desc
                )
            
        
        totals = {}
        for field, operations in self.group_by_aggregates.items():
            for op_name in operations.keys():
                if isinstance(operations[op_name], PostProcess):
                    agg_key = f"{field}__{op_name}"
                    values = [item[agg_key] for item in grouped_qs if agg_key in item and item[agg_key] is not None]
                    totals[agg_key] = self._apply_aggregation(values, operations[op_name].aggregate)
                else:
                    agg_key = f"{field}__{op_name}"
                    values = [item[agg_key] for item in grouped_qs if agg_key in item and item[agg_key] is not None]
                    if op_name == 'avg':
                        totals[agg_key] = self._apply_aggregation(values, 'avg')
                    else:
                        totals[agg_key] = self._apply_aggregation(values, 'sum')
        
        groupby_field_names = []
        fields_with_choices = []
        boolean_fields = []
        groupby_field_info = []
        
        for field_spec in groupby_fields:
            field_name, date_part = self._parse_date_field(field_spec)
            field_obj = self.model._meta.get_field(field_name)
            
            if hasattr(field_obj, 'choices') and field_obj.choices:
                fields_with_choices.append(field_spec)
                
            if field_obj.get_internal_type() == 'BooleanField':
                boolean_fields.append(field_spec)
            
            verbose_name = None
            if date_part:
                # For date fields, create a descriptive name
                base_verbose_name = str(field_obj.verbose_name) if hasattr(field_obj, 'verbose_name') and field_obj.verbose_name else field_name.replace('_', ' ')
                # Format date part names nicely
                date_part_display = {
                    'year': 'Y',
                    'month': 'M',
                    'day': 'D',
                    'week': 'W',
                    'quarter': 'Q',
                    'iso_week': 'ISO W',
                    'weekday': 'DoW',
                    'hour': 'Hr'
                }.get(date_part, date_part.replace('_', ' ').title())
                verbose_name = f"{base_verbose_name} ({date_part_display})"
                groupby_field_names.append(verbose_name)
            elif hasattr(field_obj, 'verbose_name') and field_obj.verbose_name:
                verbose_name = str(field_obj.verbose_name)
                groupby_field_names.append(verbose_name)
            else:
                verbose_name = field_spec.replace('_', ' ').title()
                groupby_field_names.append(verbose_name)
                
            # Generate sorting URLs for this groupby field
            stripped_original_param = original_sort_param.replace('-', '') if original_sort_param else ''
            is_current_sort = stripped_original_param == field_spec
            is_descending = original_sort_param.startswith('-') if original_sort_param else False
            
            url_primary = cl.get_query_string({
                'sort': field_spec
            })
            
            if is_current_sort:
                if is_descending:
                    toggle_sort_param = field_spec
                else:
                    toggle_sort_param = f"-{field_spec}"
            else:
                toggle_sort_param = field_spec
            
            url_toggle = cl.get_query_string({
                'sort': toggle_sort_param
            })
            
            groupby_field_info.append({
                'field': field_spec,
                'verbose_name': verbose_name,
                'sortable': True,
                'sorted': sort_field == field_spec,
                'sort_direction': 'descending' if sort_direction == 'descending' and sort_field == field_spec else 'ascending',
                'url_primary': url_primary,
                'url_toggle': url_toggle
            })
        
        aggregate_info = []
        for field, operations in self.group_by_aggregates.items():
            for op_name in operations.keys():
                agg_key = f"{field}__{op_name}"
                
                is_post_process = isinstance(operations[op_name], PostProcess)
                
                if is_post_process:
                    pp_obj = operations[op_name]
                    verbose_name = pp_obj.extra.get('verbose_name')
                    label = verbose_name if verbose_name else f"{op_name.capitalize()} {field.replace('_', ' ')}"
                else:
                    agg_func = operations[op_name]
                    verbose_name = None
                    
                    if hasattr(agg_func, 'extra') and isinstance(agg_func.extra, dict):
                        verbose_name = agg_func.extra.get('verbose_name')
                        if not verbose_name and 'extra' in agg_func.extra and isinstance(agg_func.extra['extra'], dict):
                            verbose_name = agg_func.extra['extra'].get('verbose_name')
                    
                    if verbose_name:
                        label = str(verbose_name)
                    else:
                        if field == 'id' and op_name == 'count':
                            label = "Count"
                        else:
                            label = f"{op_name.capitalize()} {field.replace('_', ' ')}"
                
                stripped_original_param = original_sort_param.replace('-', '') if original_sort_param else ''
                is_current_sort = stripped_original_param == agg_key
                is_descending = original_sort_param.startswith('-') if original_sort_param else False
                
                url_primary = cl.get_query_string({
                    'sort': agg_key
                })
                
                if is_current_sort:
                    if is_descending:
                        toggle_sort_param = agg_key
                    else:
                        toggle_sort_param = f"-{agg_key}"
                else:
                    toggle_sort_param = agg_key
                
                url_toggle = cl.get_query_string({
                    'sort': toggle_sort_param
                })
                
                aggregate_info.append({
                    'key': agg_key,
                    'field': field,
                    'operation': op_name,
                    'label': label,
                    'is_post_process': is_post_process,
                    'sortable': True,
                    'sorted': sort_field == agg_key,
                    'sort_direction': 'descending' if sort_direction == 'descending' and sort_field == agg_key else 'ascending',
                    'url_primary': url_primary,
                    'url_toggle': url_toggle
                })
        
        class ChangeListTotals:
            def __init__(self, original_cl, **kwargs):
                for attr in dir(original_cl):
                    if not attr.startswith('__') and not callable(getattr(original_cl, attr)) and attr != 'result_list':
                        setattr(self, attr, getattr(original_cl, attr))
                
                for key, value in kwargs.items():
                    setattr(self, key, value)
                
                if not hasattr(self, 'formset'):
                    self.formset = None
                if not hasattr(self, 'result_hidden_fields'):
                    self.result_hidden_fields = []
                
                self.get_query_string = original_cl.get_query_string
                
                if hasattr(original_cl, 'get_ordering_field_columns'):
                    self.get_ordering_field_columns = original_cl.get_ordering_field_columns
                
                self.result_list = []
        
        cl_totals = ChangeListTotals(
            cl,
            grouped_results=grouped_qs,
            groupby_fields=groupby_fields,
            groupby_field_names=groupby_field_names,
            groupby_field_info=groupby_field_info,
            fields_with_choices=fields_with_choices,
            boolean_fields=boolean_fields,
            aggregate_info=aggregate_info,
            totals=totals,
            model=self.model,
            queryset=queryset,
            params=cl.params,
            date_hierarchy=getattr(cl, 'date_hierarchy', None),
            result_list=[],
            paginator=None,
            show_all=True,
            show_full_result_count=False,
            result_count=0
        )
        
        # Create a mapping from field_spec to values_field for template usage
        field_mapping = {}
        for i, field_spec in enumerate(groupby_fields):
            field_mapping[field_spec] = values_fields[i]
        
        context = {
            **self.admin_site.each_context(request),
            'cl': cl_totals,
            'grouped_results': grouped_qs,
            'groupby_fields': groupby_fields,
            'groupby_field_names': groupby_field_names,
            'groupby_field_info': groupby_field_info,
            'fields_with_choices': fields_with_choices,
            'aggregate_info': aggregate_info,
            'totals': totals,
            'title': f"{self.model._meta.verbose_name.title()} Groups",
            'is_popup': cl.is_popup,
            'model_admin': self,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'field_mapping': field_mapping,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return TemplateResponse(request, self.change_list_template, context)