import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("smtp_service")

# Получаем настройки SMTP из переменных окружения
# Используем значения по умолчанию для обязательных параметров
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "Zooracle")

# Логирование загруженных настроек SMTP
logger.info(f"SMTP настройки: Сервер={SMTP_SERVER}, Порт={SMTP_PORT}, Пользователь={SMTP_USERNAME}, Имя отправителя={SMTP_SENDER_NAME}")
logger.info(f"Пароль задан: {'Да' if SMTP_PASSWORD else 'Нет'}")


def send_password_reset_email(email: str, reset_url: str) -> bool:
    """
    Отправляет письмо для сброса пароля
    
    Args:
        email (str): Email получателя
        reset_url (str): URL для сброса пароля
        
    Returns:
        bool: True, если письмо успешно отправлено, иначе False
    """
    logger.info(f"Запрос на отправку письма для сброса пароля на {email}")
    logger.info(f"URL для сброса: {reset_url}")
    
    # Проверка наличия настроек SMTP
    if not SMTP_SERVER:
        logger.error("Не задан SMTP сервер!")
        return False
    
    if not SMTP_USERNAME:
        logger.error("Не задано имя пользователя SMTP!")
        return False
    
    if not SMTP_PASSWORD:
        logger.error("Не задан пароль SMTP!")
        return False
    
    try:
        # Создаем объект сообщения
        message = MIMEMultipart()
        message["From"] = f"{SMTP_SENDER_NAME} <{SMTP_USERNAME}>"
        message["To"] = email
        message["Subject"] = "Восстановление пароля Zooracle"
        
        # Формируем HTML-текст письма
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white !important;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Восстановление пароля</h2>
                </div>
                <p>Здравствуйте!</p>
                <p>Вы получили это письмо, потому что запросили сброс пароля для вашей учетной записи в приложении Zooracle.</p>
                <p>Для сброса пароля нажмите на кнопку ниже:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Сбросить пароль</a>
                </div>
                
                <p>Если вы не можете нажать на кнопку, скопируйте следующую ссылку в адресную строку браузера:</p>
                <p>{reset_url}</p>
                
                <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
                <p>Ссылка для сброса пароля действительна в течение 24 часов.</p>
                
                <div class="footer">
                    <p>&copy; {datetime.now().year} Zooracle. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Прикрепляем HTML-текст
        message.attach(MIMEText(html, "html"))
        
        # Логирование попытки отправки письма
        logger.info(f"Попытка отправить письмо на {email} через {SMTP_SERVER}:{SMTP_PORT}")
        
        try:
            # Устанавливаем соединение с SMTP-сервером
            logger.debug(f"Устанавливаем соединение с {SMTP_SERVER}:{SMTP_PORT}")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            
            # Включаем расширенное логирование для отладки
            server.set_debuglevel(1)
            
            # Определяем поддерживаемые расширения SMTP
            server.ehlo()
            if server.has_extn('STARTTLS'):
                logger.debug("Начинаем TLS шифрование")
                server.starttls()  # Включаем шифрование
                server.ehlo()  # Повторно представляемся после TLS
            else:
                logger.warning("Сервер не поддерживает STARTTLS!")
            
            # Проверка поддержки аутентификации
            if server.has_extn('AUTH'):
                logger.debug("Выполняем аутентификацию")
                # Аутентификация
                try:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    logger.info("Аутентификация успешна")
                except smtplib.SMTPAuthenticationError as auth_err:
                    logger.error(f"Ошибка аутентификации: {auth_err}")
                    server.quit()
                    return False
            else:
                logger.warning("Сервер не поддерживает аутентификацию!")
            
            # Отправляем письмо
            logger.debug(f"Отправляем письмо от {message['From']} к {message['To']}")
            server.send_message(message)
            logger.info(f"Письмо успешно отправлено на {email}")
            
            # Закрываем соединение
            server.quit()
            logger.debug("Соединение с SMTP-сервером закрыто")
            
            return True
        except smtplib.SMTPHeloError:
            logger.error("Сервер не ответил должным образом на HELO")
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"Сервер отклонил всех получателей: {email}")
            return False
        except smtplib.SMTPSenderRefused:
            logger.error(f"Сервер отклонил отправителя: {SMTP_USERNAME}")
            return False
        except smtplib.SMTPDataError:
            logger.error("Сервер ответил, что данные некорректны")
            return False
        except smtplib.SMTPNotSupportedError:
            logger.error("Команда не поддерживается SMTP-сервером")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Необработанная ошибка SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отправке письма: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при подготовке письма: {str(e)}", exc_info=True)
        return False


# Проверка окружения при запуске модуля
def check_environment():
    """
    Проверяет настройки SMTP при инициализации модуля и логирует предупреждения при проблемах
    """
    issues = []
    
    if not SMTP_SERVER:
        issues.append("SMTP_SERVER не задан")
    
    if not SMTP_PORT:
        issues.append("SMTP_PORT не задан или некорректен")
    
    if not SMTP_USERNAME:
        issues.append("SMTP_USERNAME не задан")
    
    if not SMTP_PASSWORD:
        issues.append("SMTP_PASSWORD не задан")
    
    if issues:
        logger.warning("Обнаружены проблемы с SMTP-настройками:")
        for issue in issues:
            logger.warning(f" - {issue}")
        logger.warning("Функциональность восстановления пароля может быть недоступна")
    else:
        logger.info("SMTP-настройки успешно загружены")


# Проверяем настройки SMTP при импорте модуля
check_environment()