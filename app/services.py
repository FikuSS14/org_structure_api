import logging
from django.core.exceptions import ValidationError
from .models import Department

logger = logging.getLogger(__name__)


def check_for_cycle(new_parent_id: int | None, current_dept_id: int | None) -> bool:
    """
    ПРОВЕРКА НА ЦИКЛЫ В ДЕРЕВЕ ПОДРАЗДЕЛЕНИЙ

    Возвращает True, если цикла НЕТ (можно менять parent).
    Возвращает False, если цикл ОБНАРУЖЕН (нельзя менять parent).
    """
    if not new_parent_id:
        logger.info(f"Department {current_dept_id}: parent removed, no cycle possible")
        return True

    if not current_dept_id:
        logger.info(f"Creating new department with parent {new_parent_id}, no cycle check needed")
        return True

    if new_parent_id == current_dept_id:
        logger.warning(f"Cycle detected: Department {current_dept_id} cannot be parent of itself")
        return False

    try:
        current_dept = Department.objects.get(id=current_dept_id)
    except Department.DoesNotExist:
        logger.error(f"Current department {current_dept_id} not found")
        return False

    descendants = current_dept.get_descendants_ids()
    logger.info(f"Department {current_dept_id} has descendants: {descendants}")

    if new_parent_id in descendants:
        logger.warning(
            f"Cycle detected: Department {new_parent_id} is a descendant of {current_dept_id}"
        )
        return False

    logger.info(f"No cycle detected for department {current_dept_id}")
    return True


def reassign_employees(department: Department, new_department_id: int):
    """
    Переводит всех сотрудников из удаляемого подразделения в новое.
    """
    try:
        new_dept = Department.objects.get(id=new_department_id)
        count = department.employees.update(department=new_dept)
        logger.info(f"Reassigned {count} employees from dept {department.id} to {new_department_id}")
        return count
    except Department.DoesNotExist:
        logger.error(f"Target department {new_department_id} not found for reassign")
        raise ValidationError(f"Подразделение {new_department_id} не существует")