#!/usr/bin/env python3
"""
IMS Backend Project Setup Script
This script sets up the Django backend for the Inventory Management System
Note: This is a project setup script, not a package setup file.
"""
def get_version():
def run_command(command, description=""):
def create_env_file():
def create_superuser():
def collect_static():
def install_requirements():
def setup_redis():
def setup_ocr():
def main():

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