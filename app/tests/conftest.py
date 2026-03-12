import pytest
from rest_framework.test import APIClient
from app.models import Department, Employee


@pytest.fixture
def api_client():
    """
    API клиент для отправки запросов
    """
    return APIClient()


@pytest.fixture
def department():
    """тестовое подразделение
    """
    return Department.objects.create(name="IT Department")


@pytest.fixture
def employee(department):
    """
    тестовый сотрудник
    """
    return Employee.objects.create(
        department=department,
        full_name="John Doe",
        position="Python Developer"
    )


@pytest.fixture
def create_departments():
    """
    helper для создания нескольких подразделений
    """
    def _create_departments(count=3):
        departments = []
        for i in range(count):
            dept = Department.objects.create(name=f"Department {i+1}")
            departments.append(dept)
        return departments
    return _create_departments