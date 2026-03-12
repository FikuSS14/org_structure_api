import logging
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError

from .models import Department, Employee
from .serializers import (
    DepartmentSerializer,
    DepartmentTreeSerializer,
    EmployeeSerializer
)
from .services import check_for_cycle, reassign_employees

logger = logging.getLogger(__name__)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления подразделениями.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def create(self, request, *args, **kwargs):
        """POST /departments/"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        logger.info(f"Department created: {serializer.data['id']}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """GET /departments/{id}/"""
        instance = self.get_object()
        try:
            depth = int(request.query_params.get('depth', 1))
            depth = max(1, min(5, depth))
        except (ValueError, TypeError):
            depth = 1
        include_employees = request.query_params.get('include_employees', 'true').lower() == 'true'
        
        serializer = DepartmentTreeSerializer(
            instance,
            context={
                'max_depth': depth,
                'current_depth': 0,
                'include_employees': include_employees
            }
        )
        return Response(serializer.data)

    def _check_parent_cycle(self, instance, new_parent_id):
        """Вспомогательный метод: проверка циклов"""
        if new_parent_id is None:
            return True
        if new_parent_id == instance.id:
            return False
        return check_for_cycle(new_parent_id, instance.id)

    def update(self, request, *args, **kwargs):
        """PUT /departments/{id}/"""
        instance = self.get_object()
        
        if 'parent' in request.data:
            parent_value = request.data.get('parent')
            if parent_value is not None:
                try:
                    parent_id = int(parent_value)
                except (ValueError, TypeError):
                    parent_id = None
            else:
                parent_id = None
            
            if parent_id is not None:
                if not self._check_parent_cycle(instance, parent_id):
                    return Response(
                        {"error": "Обнаружен цикл в структуре подразделений"},
                        status=status.HTTP_409_CONFLICT
                    )
        
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /departments/{id}/"""
        instance = self.get_object()

        if 'parent' in request.data:  
            parent_value = request.data.get('parent')
            if parent_value is not None:
                try:
                    parent_id = int(parent_value)
                except (ValueError, TypeError):
                    parent_id = None
            else:
                parent_id = None
            
            if parent_id is not None:
                if not self._check_parent_cycle(instance, parent_id):
                    return Response(
                        {"error": "Обнаружен цикл в структуре подразделений"},
                        status=status.HTTP_409_CONFLICT
                    )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """DELETE /departments/{id}/"""
        instance = self.get_object()
        mode = request.query_params.get('mode', 'cascade')
        
        if mode == 'cascade':
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif mode == 'reassign':
            reassign_to_id = request.query_params.get('reassign_to_department_id')
            if not reassign_to_id:
                return Response(
                    {"error": "reassign_to_department_id обязателен при mode=reassign"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                reassign_employees(instance, int(reassign_to_id))
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"error": f"Неизвестный режим удаления: {mode}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='employees')
    def create_employee(self, request, pk=None):
        """POST /departments/{id}/employees/"""
        department = self.get_object()
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(department_id=department.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления сотрудниками."""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer