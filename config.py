"""Значения конфигурации, загружаемые из переменных окружения.

Секреты (пароли, логины, URI) читаются из переменных окружения. Для
локальной разработки можно создать файл `.env` и поместить туда нужные
переменные — этот файл не должен попадать в репозиторий с реальными
секретами. В проекте есть пример `.env.example` с перечнем переменных.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из директории рядом с этим файлом (удобство для разработки).
# Явный путь предотвращает проблемы, когда процесс запускается из другой
# рабочей директории.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Параметры подключения к MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "ich-db.edu.itcareerhub.de")
MYSQL_USER = os.getenv("MYSQL_USER", "ich1")
# По соображениям безопасности по умолчанию пароль пуст — не храните
# реальные пароли в репозитории
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB", "sakila")

# Части для формирования строки подключения к MongoDB. URI собирается
# кодом, который использует эти переменные; убедитесь, что `MONGO_USER`
# и `MONGO_PASS` заданы в окружении при необходимости.
MONGO_URI_PREFIX = os.getenv("MONGO_URI_PREFIX", "mongodb+srv://")
MONGO_URI_SUFFIX = os.getenv("MONGO_URI_SUFFIX", "@cluster0.ycgtzbd.mongodb.net/")
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASS = os.getenv("MONGO_PASS", "")
MONGO_DB = os.getenv("MONGO_DB", "movie_logs")
MONGO_COLL = os.getenv("MONGO_COLL", "final_project_dam130625_alexver")

# Параметры приложения по умолчанию
LIMIT = int(os.getenv("LIMIT", "10"))

# Настраиваемый порядок рейтингов (от мягкого к строгому).
RATING_ORDER = list("G,PG,PG-13,R,NC-17") 
