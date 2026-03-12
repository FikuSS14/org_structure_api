# Org Structure API

API для управления организационной структурой компании (подразделения + сотрудники).

---

## Структура проекта

```
org_structure_api/
├── app/
│   ├── models.py          # Модели Department и Employee
│   ├── serializers.py     # Валидация и сериализация
│   ├── views.py           # ViewSet с бизнес-логикой
│   ├── services.py        # Проверка циклов, reassign
│   ├── urls.py            # Роутинг
│   └── tests/             # Тесты (pytest)
├── org_structure_api/
│   ├── settings.py        # Настройки Django
│   └── urls.py            # Главные URL
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```
---

## Быстрый старт

### Требования
- Docker
- Docker Compose

### Клонировать репозиторий
git clone https://github.com/FikuSS14/org_structure_api.git

cd org_structure_api

### Запустить через Docker
docker-compose up --build

### Swagger документация:
http://localhost:8000/api/docs/

### Django Admin:
http://localhost:8000/admin/

---

## Запустить все тесты
docker-compose exec web pytest -v

---

## API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/departments/` | Создать подразделение |
| GET | `/api/departments/{id}/` | Получить подразделение + дерево |
| PATCH | `/api/departments/{id}/` | Обновить подразделение |
| DELETE | `/api/departments/{id}/?mode=cascade\|reassign` | Удалить подразделение |
| POST | `/api/departments/{id}/employees/` | Создать сотрудника |

---

## Технологии

- **Backend:** Django 4.2 + Django REST Framework
- **База данных:** PostgreSQL 15
- **Контейнеризация:** Docker + docker-compose
- **Тестирование:** pytest + pytest-django
- **Документация:** drf-spectacular (OpenAPI 3.0 / Swagger)
