"""Параметры конфигурации, загружаемые из переменных окружения.

Секреты (пароли, логины, URI) читаются из переменных окружения.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из директории рядом с этим файлом.

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Параметры подключения к MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASS = os.getenv("MYSQL_PASS")
MYSQL_DB = os.getenv("MYSQL_DB")

# Части для формирования строки подключения к MongoDB. URI собирается
# кодом, который использует эти переменные
MONGO_URI_PREFIX = os.getenv("MONGO_URI_PREFIX")
MONGO_URI_SUFFIX = os.getenv("MONGO_URI_SUFFIX")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLL = os.getenv("MONGO_COLL")
# Параметры приложения по умолчанию
LIMIT = int(os.getenv("LIMIT"))

# Настраиваемый порядок рейтингов (от мягкого к строгому).
RATING_ORDER = ["G","PG","PG-13","R","NC-17"] 

# Описания рейтингов на русском языке. Ключи — коды рейтингов в БД.
RATING_DESCRIPTIONS = {
	"G": "Для всей аудитории",
	"PG": "Рекомендуется родительский контроль",
	"PG-13": "Для зрителей старше 13 лет; родительский контроль рекомендуется",
	"R": "Только для взрослой аудитории; возрастное ограничение 17+",
	"NC-17": "Строго 18+; не предназначено для детей",
}
