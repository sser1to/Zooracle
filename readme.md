# Zooracle
**Основной функционал:**
- Управление доступом (регистрация, аутентификация, сессии)
- Каталог животных (просмотр, поиск и фильтрация)
- Добавление/редактирование/удаление видов животных
- Создание/редактирование тестов на знаение животных
- Прохождение тестов на знание животных
- Личный кабинет (изменение личной информации, просмотр статистики)

<img src="https://github.com/user-attachments/assets/22bae035-a557-4b6a-89cc-77b1ad90278b" alt="изображение">
<p><em>Главная страница (каталог)</em></p>

**Стек:**
- Фронтенд: **Vue.js**
- Бэкенд: **Python + FastAPI**
- База данных: **PostgreSQL**
- Файловое хранилище: **S3 Cloud Storage**
- Конейнеризация: **Docker**

## Начало работы
1. Клонируем репозиторий
```
git clone https://github.com/sser1to/Zooracle.git
```
2. Создаем файл `.env` в корневой директории проекта на основе `.env.example` и вносим туда свои переменные для:
- подключения к базе данных
- настройки S3 Cloud Storage
- SMTP-сервера
- домена приложения 
3. В папку `ssl` помещаем SSL-сертификат:
- `certificate_ca.crt` - корневой сертификат
- `certificate.crt` - сертификат
- `certificate.key` - ключ
4. Запускаем docker-compose
```
docker compose up -d
```
5. Переходим на сайт (домен указывается в `.env`)
```
https://your_domain.com
```
**Готово!**
