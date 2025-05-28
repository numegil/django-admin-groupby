# Django Admin Group-By

Django Admin Group-By adds SQL-style `GROUP BY` functionality to the Django admin, letting you easily group and summarize data with aggregations like counts, sums, and averages directly in the admin interface.

It works by adding a "Group by" filter in the admin sidebar, allowing you to select fields and instantly see summarized views of your data.

## Key Features

* **Group Data Directly in Admin:** Easily group by model fields to quickly identify patterns.
* **Built-in Aggregations:** Perform counts, sums, averages and more including advanced custom aggregations.
* **Custom Calculations:** Aggregate calculated fields with lambda functions that run after database queries.
* **Compatible:** Integrates seamlessly with Django admin filters, search, and permissions.
* **Efficient:** Performs aggregations server-side, suitable for large datasets.

## Installation

```bash
pip install django-admin-groupby
```

Add the app to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.admin',
    # ...
    'django_admin_groupby',  # Add this line
]
```

## Example Usage

Here's an example demonstrating both basic grouping and advanced aggregations:

```python
from django.contrib import admin
from django.db.models import Count, Sum, Avg, Q
from django_admin_groupby.admin import GroupByAdminMixin
from django_admin_groupby import PostProcess
from .models import Product

@admin.register(Product)
class ProductAdmin(GroupByAdminMixin, admin.ModelAdmin):
    # ...

    group_by_fields = ['category', 'in_stock']

    # (optional, defaults to just counts if nothing is specified)
    group_by_aggregates = {
        'id': {
            'count': Count('id', extra={'verbose_name': "Total Products"}),
            'in_stock_count': Count('id', filter=Q(in_stock=True),
                                    extra={'verbose_name': "In-Stock Products"}),
        },
        'price': {
            'avg': Avg('price', extra={'verbose_name': "Average Price"}),
            'sum': Sum('price', extra={'verbose_name': "Total Value"}),
            'expensive_items': Count('id', filter=Q(price__gte=100),
                                     extra={'verbose_name': "Expensive Items (>= $100)"}),
        },
        'profit_margin': {
            'total': PostProcess(
                lambda product: product.price - product.cost,
                verbose_name="Profit Margin",
                aggregate="avg"
            )
        }
    }
```

## Demo

A demo project is included in the repository to illustrate usage:

<img width="1727" alt="Screenshot 2025-05-27 at 9 23 08 PM" src="https://github.com/user-attachments/assets/a8bc6c0c-428e-4cb3-9d26-9251964db42a" />

```bash
git clone https://github.com/numegil/django-admin-groupby.git
cd django-admin-groupby

# (optional)
python -m venv venv
source venv/bin/activate

pip install -e .
cd example
python manage.py migrate
python manage.py generate_cats --count 100
python manage.py createsuperuser
python manage.py runserver
```

Access the demo at `http://localhost:8000/admin/cats/cat/`.

## License

MIT License. Feel free to use and modify this code.
