"""Минимальный MongoDB helper.

Собирает URI и проверяет соединение при инициализации. Если подключение
выполнить не удалось, `coll` = None и логирование не производится; выводится
информационное сообщение. Это упрощает поведение и делает ошибки подключения
очевидными для оператора.
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


def _build_uri():
    env_uri = os.getenv("MONGO_URI")
    if env_uri:
        return env_uri
    if MONGO_USER and MONGO_PASS:
        return f"{MONGO_URI_PREFIX}{MONGO_USER}:{MONGO_PASS}{MONGO_URI_SUFFIX}"
    return None


_uri = _build_uri()
client = None
db = None
coll = None

if _uri:
    try:
        # Небольшой таймаут на обнаружение недоступного хоста
        client = MongoClient(_uri, serverSelectionTimeoutMS=3000)
        # Фактически проверяем соединение
        client.server_info()
        db = client[MONGO_DB]
        coll = db[MONGO_COLL]
    except Exception as exc:
        print(f"Внимание: не удалось подключиться к MongoDB ({exc}). Логирование отключено.")
        client = None
        coll = None
else:
    print("Инфо: MongoDB URI не задан (установите MONGO_URI или MONGO_USER/MONGO_PASS). Логирование отключено.")
    coll = None

