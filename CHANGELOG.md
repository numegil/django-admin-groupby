# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-06-24

### Fixed
- Fixed display of nullable boolean fields in group by view - now shows '?' icon instead of red X for None values
- Fixed filtering for nullable boolean fields - clicking on None values now correctly filters with `field__isnull=True`

## [1.0.0] - 2025-05-27

### Added
- Initial stable release of django-admin-groupby
- Group by functionality for Django admin with SQL-style aggregations
- Support for Count, Sum, Avg aggregations
- Custom PostProcess aggregations for calculated fields
- Integration with Django admin filters, search, and permissions
- Example project demonstrating usage with a Cat model
- Support for Django 3.2 through 5.2
- Python 3.8 through 3.12 support
