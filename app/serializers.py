from rest_framework import serializers
from .models import Department, Employee


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сотрудника.
    """
    class Meta:
        model = Employee
        fields = ['id', 'department_id', 'full_name', 'position', 'hired_at', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_full_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("full_name не может быть пустым")
        value = value.strip()
        if len(value) > 200:
            raise serializers.ValidationError("full_name не может превышать 200 символов")
        return value

    def validate_position(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("position не может быть пустым")
        value = value.strip()
        if len(value) > 200:
            raise serializers.ValidationError("position не может превышать 200 символов")
        return value


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для подразделения.
    """
    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("name не может быть пустым")
        value = value.strip()
        if len(value) > 200:
            raise serializers.ValidationError("name не может превышать 200 символов")
        return value


class DepartmentTreeSerializer(DepartmentSerializer):
    """
    Расширенный сериализатор для дерева подразделений.
    """
    employees = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['employees', 'children']

    def get_employees(self, obj):
        if not self.context.get('include_employees', True):
            return []
        employees = obj.employees.all().order_by('created_at')
        return EmployeeSerializer(employees, many=True).data

    def get_children(self, obj):
        max_depth = self.context.get('max_depth', 1)
        current_depth = self.context.get('current_depth', 0)

        if current_depth >= max_depth:
            return []

        children = obj.children.all()
        result = []
        for child in children:
            child_serializer = DepartmentTreeSerializer(
                child,
                context={
                    'max_depth': max_depth,
                    'current_depth': current_depth + 1,
                    'include_employees': self.context.get('include_employees', True)
                }
            )
            result.append(child_serializer.data)
        return result