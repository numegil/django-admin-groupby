# Date Grouping Implementation Plan

## Overview
Add support for grouping by date parts in django-admin-groupby using Django's standard lookup syntax (e.g., `created_date__year`).

## Implementation Steps

### 1. Parse field__year syntax and extract field name + date part
- Add helper method to detect `field__year` pattern
- Return tuple: (field_name, date_part)
- Keep original field name for non-date fields
- ~10 lines of code

### 2. Build Django ORM annotation for year extraction
- Create method to build Django `Extract('field', 'year')` annotation
- Handle annotation naming for the queryset
- ~15 lines of code

### 3. Integrate year extraction into existing queryset building
- Modify queryset building section to use date extraction
- Update `values()` call to use the annotation
- Ensure compatibility with existing aggregations
- ~20-30 lines of modifications

### 4. Test with basic year grouping
- Test with a simple model having a date field
- Verify year grouping works
- Check that non-date fields still work

### 5. Add support for month, day, week, and quarter extraction
- Extend parser to handle `__month`, `__day`, `__week`, `__quarter`
- Add mapping of date parts to Django functions
- ~20 lines

### 6. Implement proper date formatting in the grouped results display
- Add formatter for date groups (e.g., "2024" for years, "January" for months)
- Update template context to use formatted values
- ~30 lines

### 7. Add date range filtering when clicking on grouped date values
- Modify filter URL generation for date groups
- Convert year group → `field__year=2024`
- Convert month group → `field__year=2024&field__month=1`
- ~40 lines

## Usage Examples

After implementation, developers will be able to use:

```python
class MyModelAdmin(GroupByAdminMixin, admin.ModelAdmin):
    group_by_fields = [
        'created_date__year',
        'created_date__month',
        'updated_date__quarter',
        'status',  # Regular fields still work
    ]
```

## Notes
- Each step builds on the previous one
- Repository remains fully functional after each step
- Following Django's existing lookup syntax for familiarity