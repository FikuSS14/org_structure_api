import pytest
from app.models import Department, Employee


@pytest.mark.django_db
class TestDepartmentAPI:
    """
    Тесты для API подразделений
    """

    def test_create_department_success(self, api_client):
        """POST /departments/ - успешное создание подразделения"""
        response = api_client.post('/api/departments/', {
            'name': 'Backend Team'
        })
        assert response.status_code == 201
        assert response.data['name'] == 'Backend Team'
        assert Department.objects.filter(id=response.data['id']).exists()

    def test_create_department_with_parent(self, api_client, department):
        response = api_client.post('/api/departments/', {
            'name': 'Sub Team',
            'parent': department.id  
        })
        assert response.status_code == 201
        assert response.data['parent'] == department.id  

    def test_create_department_empty_name(self, api_client):
        """ POST /departments/ - пустое название (валидация)"""
        response = api_client.post('/api/departments/', {
            'name': ''
        })
        assert response.status_code == 400

    def test_create_department_self_parent(self, api_client, department):
        response = api_client.post('/api/departments/', {
            'name': 'Test',
            'parent': department.id  
        })
        assert response.status_code == 201

    def test_update_department_prevent_cycle(self, api_client, department):
        """PATCH /departments/{id}/ - защита от цикла (сам себе родитель)"""
        response = api_client.patch(f'/api/departments/{department.id}/', {
            'parent': department.id
        })
        assert response.status_code == 409

    def test_get_department_with_tree(self, api_client, department):
        """GET /departments/{id}/ - получение с деревом подразделений"""
        child = Department.objects.create(name='Child Dept', parent=department)
        
        response = api_client.get(f'/api/departments/{department.id}/?depth=2')
        assert response.status_code == 200
        assert len(response.data['children']) == 1
        assert response.data['children'][0]['name'] == 'Child Dept'

    def test_get_department_with_employees(self, api_client, department, employee):
        """GET /departments/{id}/ - с сотрудниками"""
        response = api_client.get(f'/api/departments/{department.id}/?depth=1&include_employees=true')
        assert response.status_code == 200
        assert len(response.data['employees']) == 1
        assert response.data['employees'][0]['full_name'] == 'John Doe'

    def test_get_department_without_employees(self, api_client, department, employee):
        """GET /departments/{id}/ - без сотрудников"""
        response = api_client.get(f'/api/departments/{department.id}/?depth=1&include_employees=false')
        assert response.status_code == 200
        assert response.data['employees'] == []

    def test_delete_department_cascade(self, api_client, department, employee):
        """DELETE /departments/{id}/?mode=cascade - каскадное удаление"""
        response = api_client.delete(f'/api/departments/{department.id}/?mode=cascade')
        assert response.status_code == 204
        assert Department.objects.filter(id=department.id).exists() is False
        assert Employee.objects.filter(id=employee.id).exists() is False

    def test_delete_department_reassign(self, api_client, department, employee):
        """DELETE /departments/{id}/?mode=reassign - перевод сотрудников"""
        new_dept = Department.objects.create(name='New Department')
        
        response = api_client.delete(
            f'/api/departments/{department.id}/?mode=reassign&reassign_to_department_id={new_dept.id}'
        )
        assert response.status_code == 204
        assert Department.objects.filter(id=department.id).exists() is False
        
        employee.refresh_from_db()
        assert employee.department.id == new_dept.id

    def test_delete_department_reassign_missing_param(self, api_client, department):
        """DELETE /departments/{id}/?mode=reassign - без reassign_to_department_id"""
        response = api_client.delete(f'/api/departments/{department.id}/?mode=reassign')
        assert response.status_code == 400

    def test_cycle_prevention_in_tree(self, api_client):
        """Проверка: нельзя создать цикл в дереве"""
        dept_a = Department.objects.create(name='A')
        dept_b = Department.objects.create(name='B', parent=dept_a)
        dept_c = Department.objects.create(name='C', parent=dept_b)
        
        response = api_client.patch(f'/api/departments/{dept_a.id}/', {
            'parent': dept_c.id
        })
        assert response.status_code == 409


@pytest.mark.django_db
class TestEmployeeAPI:
    """
    Тесты для API сотрудников
    """

    def test_create_employee_success(self, api_client, department):
        """POST /departments/{id}/employees/ - успешное создание"""
        response = api_client.post(f'/api/departments/{department.id}/employees/', {
            'full_name': 'Jane Smith',
            'position': 'Senior Developer'
        })
        assert response.status_code == 201
        assert response.data['full_name'] == 'Jane Smith'

    def test_create_employee_in_nonexistent_department(self, api_client):
        """POST в несуществующее подразделение - 404"""
        response = api_client.post('/api/departments/9999/employees/', {
            'full_name': 'Jane Doe',
            'position': 'Manager'
        })
        assert response.status_code == 404

    def test_create_employee_empty_name(self, api_client, department):
        """POST /employees/ - пустое имя (валидация)"""
        response = api_client.post(f'/api/departments/{department.id}/employees/', {
            'full_name': '',
            'position': 'Developer'
        })
        assert response.status_code == 400

    def test_create_employee_empty_position(self, api_client, department):
        """POST /employees/ - пустая должность (валидация)"""
        response = api_client.post(f'/api/departments/{department.id}/employees/', {
            'full_name': 'John Doe',
            'position': ''
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestDepartmentDepth:
    """
    Тесты для проверки глубины дерева
    """

    def test_depth_limit(self, api_client):
        """depth=5 (максимум)"""
        root = Department.objects.create(name='Root')
        child1 = Department.objects.create(name='Child1', parent=root)
        child2 = Department.objects.create(name='Child2', parent=child1)
        child3 = Department.objects.create(name='Child3', parent=child2)
        child4 = Department.objects.create(name='Child4', parent=child3)
        child5 = Department.objects.create(name='Child5', parent=child4)
        
        response = api_client.get(f'/api/departments/{root.id}/?depth=5')
        assert response.status_code == 200
        assert len(response.data['children']) == 1

    def test_depth_default(self, api_client):
        """depth по умолчанию = 1"""
        root = Department.objects.create(name='Root')
        child = Department.objects.create(name='Child', parent=root)
        grandchild = Department.objects.create(name='Grandchild', parent=child)
        
        response = api_client.get(f'/api/departments/{root.id}/')
        assert response.status_code == 200
        assert len(response.data['children']) == 1
        assert response.data['children'][0].get('children', []) == []

