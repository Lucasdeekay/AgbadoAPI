"""
Setup script for AgbadoAPI.

This script enables the project to be installed as a package
and provides metadata for distribution.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    """Read the README.md file."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    """Read requirements from requirements.txt."""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="agbado-api",
    version="1.3.0",
    description="A comprehensive Django REST API for the Agbado platform with optimized performance and enhanced security",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Agbado Development Team",
    author_email="dev@agbado.com",
    url="https://github.com/agbado/agbado-api",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="django, rest, api, authentication, wallet, tasks, rewards, services, providers, notifications",
    project_urls={
        "Bug Reports": "https://github.com/agbado/agbado-api/issues",
        "Source": "https://github.com/agbado/agbado-api",
        "Documentation": "https://agbado-api.readthedocs.io/",
        "Changelog": "https://github.com/agbado/agbado-api/blob/main/CHANGELOG.md",
    },
    entry_points={
        "console_scripts": [
            "agbado-api=agbado.manage:main",
        ],
    },
    zip_safe=False,
    extras_require={
        "dev": [
            "pytest>=7.4.3,<8.0",
            "pytest-django>=4.7.0,<5.0",
            "pytest-cov>=4.1.0,<5.0",
            "factory-boy>=3.3.0,<4.0",
            "faker>=20.1.0,<21.0",
            "black>=23.11.0,<24.0",
            "flake8>=6.1.0,<7.0",
            "isort>=5.12.0,<6.0",
            "mypy>=1.7.1,<2.0",
            "pylint>=3.0.3,<4.0",
            "django-debug-toolbar>=4.2.0,<5.0",
            "django-extensions>=3.2.3,<4.0",
            "bandit>=1.7.5,<2.0",
            "safety>=2.3.5,<3.0",
            "django-silk>=5.0.4,<6.0",
            "drf-spectacular>=0.26.5,<1.0",
            "sentry-sdk>=1.38.0,<2.0",
        ],
    },
) 