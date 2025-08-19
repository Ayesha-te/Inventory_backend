#!/usr/bin/env python3
"""
IMS Backend Project Setup Script
This script sets up the Django backend for the Inventory Management System
Note: This is a project setup script, not a package setup file.
"""

from setuptools import setup, find_packages

setup(
    name="ims-backend",
    version="1.0.0",
    description="Inventory Management System Backend (Django)",
    author="Ayesha Jahangir",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],  # Requirements are read from requirements.txt or specify here
    python_requires='>=3.11',
)