from django.db import models
from django.core.exceptions import ValidationError


class Department(models.Model):
    """
    Подразделение компании
    Может иметь родительское подразделение (строим дерево)
    """
    name = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        help_text="Название подразделения"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Родительское подразделение"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата создания"
    )

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'parent'],
                name='unique_department_name_per_parent'
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """
        Валидация на уровне модели
        Нельзя сделать подразделение родителем самого себя.
        """
        if self.parent_id == self.id:
            raise ValidationError("Подразделение не может быть родителем самого себя")

    def get_descendants_ids(self):
        """
        Рекурсивно получает ID всех потомков подразделения.
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child.id)
            descendants.extend(child.get_descendants_ids())
        return descendants


class Employee(models.Model):
    """
    Сотрудник компании.
    Принадлежит одному подразделению.
    """
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='employees',
        help_text="Подразделение сотрудника"
    )
    full_name = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        help_text="ФИО сотрудника"
    )
    position = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        help_text="Должность"
    )
    hired_at = models.DateField(
        null=True,
        blank=True,
        help_text="Дата найма (опционально)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата создания записи"
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['created_at']  

    def __str__(self):
        return f"{self.full_name} ({self.position})"
    
    def get_descendants_ids(self):
        """
        Рекурсивно получает ID всех потомков подразделения.
        """
        descendants = []
        children = list(self.children.all())
        
        for child in children:
            descendants.append(child.id)
            descendants.extend(child.get_descendants_ids())
        
        return descendants