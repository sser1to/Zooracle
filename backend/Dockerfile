FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY backend/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы приложения
COPY backend/app ./app

# Создаем пользователя без прав root
RUN useradd -m appuser
USER appuser

# Запускаем приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]