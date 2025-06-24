default_app_config = 'django_admin_groupby.apps.DjangoAdminGroupByConfig'
__version__ = '1.0.1'

from .aggregations import PostProcess

__all__ = ['PostProcess']