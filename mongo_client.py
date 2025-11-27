"""
Собирает URI и проверяет соединение при инициализации.
"""

import os
from pymongo import MongoClient, errors
from config import (
    MONGO_URI_PREFIX,
    MONGO_URI_SUFFIX,
    MONGO_USER,
    MONGO_PASS,
    MONGO_DB,
    MONGO_COLL,
)


_uri = f"{MONGO_URI_PREFIX}{MONGO_USER}:{MONGO_PASS}{MONGO_URI_SUFFIX}"
client = None
db = None
coll = None

if _uri:
    try:
        client = MongoClient(_uri, serverSelectionTimeoutMS=3000)
        # Проверяем соединение
        client.server_info()
        db = client[MONGO_DB]
        coll = db[MONGO_COLL]
    except Exception as exc:
        print(
            f"Внимание: не удалось подключиться к MongoDB ({exc}). Логирование отключено.")
        client = None
        coll = None
else:
    print("Инфо: MongoDB URI не задан. Логирование отключено.")
    coll = None
