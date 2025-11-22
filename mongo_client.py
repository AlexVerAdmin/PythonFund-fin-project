"""Общий клиент MongoDB и коллекция для проекта.

Централизует логику подключения к MongoDB. Поведение:
- Если задана переменная окружения `MONGO_URI`, используется она как
    полный URI.
- Иначе, если заданы `MONGO_USER` и `MONGO_PASS` в `config`, URI строится
    из префикса/суффикса.
- Если ни одного варианта нет или URI некорректен, логирование в MongoDB
    отключается, и модуль предоставляет безопасную заглушку-коллекцию,
    чтобы приложение не падало.

Это упрощает локальную разработку, когда учётные данные Mongo отсутствуют.
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
    # Предпочитаем полный URI из переменной окружения, если он задан
    env_uri = os.getenv("MONGO_URI")
    if env_uri:
        return env_uri
    # Otherwise construct from pieces only when user/pass present
    if MONGO_USER and MONGO_PASS:
        return f"{MONGO_URI_PREFIX}{MONGO_USER}:{MONGO_PASS}{MONGO_URI_SUFFIX}"
    return None


class _EmptyCursor:
    """Минимальная заглушка курсора, не возвращающая документов.

    Поддерживает вызовы `.sort()` и `.limit()`, используемые в проекте.
    """

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def __iter__(self):
        return iter(())


class _NoOpDeleteResult:
    def __init__(self):
        self.deleted_count = 0


class _SafeCollection:
    """Заглушка коллекции, выполняющая no-op операции при отключённом Mongo.

    Реализует методы, используемые в проекте: `insert_one`, `aggregate`,
    `find`, `delete_many`.
    """

    def insert_one(self, doc):
        return None

    def aggregate(self, pipeline):
        return []

    def find(self, *args, **kwargs):
        return _EmptyCursor()

    def delete_many(self, filt):
        return _NoOpDeleteResult()


_uri = _build_uri()
client = None
db = None
coll = None

if _uri:
    try:
        client = MongoClient(_uri)
        db = client[MONGO_DB]
        coll = db[MONGO_COLL]
    except errors.InvalidURI as exc:
        # Не выбрасываем исключение — делаем Mongo необязательной, но
        # информируем разработчика
        print(f"Внимание: неверный MongoDB URI: {exc}. Логирование в MongoDB отключено.")
        client = None
        coll = _SafeCollection()
else:
    # URI не задан — предоставляем безопасную заглушку-коллекцию, чтобы
    # приложение не падало
    print("Инфо: MongoDB URI не задан (установите MONGO_URI или MONGO_USER/MONGO_PASS). Логирование в MongoDB отключено.")
    coll = _SafeCollection()

