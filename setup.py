from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="django-admin-groupby",
    version="1.0.1",
    author="Alexei Gousev",
    author_email="numegil@gmail.com",
    description="A Django app that extends the admin interface with group-by functionality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/numegil/django-admin-groupby",
    project_urls={
        "Bug Tracker": "https://github.com/numegil/django-admin-groupby/issues",
        "Source Code": "https://github.com/numegil/django-admin-groupby",
        "Documentation": "https://github.com/numegil/django-admin-groupby#readme",
        "Changelog": "https://github.com/numegil/django-admin-groupby/blob/main/CHANGELOG.md",
    },
    keywords="django admin group-by groupby aggregate aggregation sum count average",
    packages=find_packages(exclude=["example", "example.*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
    ],
)