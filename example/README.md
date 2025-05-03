# Django Admin GroupBy Example

This is an example Django project that demonstrates how to use the django-admin-groupby package.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -e ..
   ```

3. Run migrations:
   ```
   python manage.py migrate
   ```

4. Create sample data:
   ```
   python manage.py generate_cats
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Visit the admin site at http://127.0.0.1:8000/admin/

## Usage

1. Log in to the admin site
2. Go to the Cats section
3. Use the "Group by" filter to group cats by color, vaccination status, or both
4. See aggregated results for count, weight, and age