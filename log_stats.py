"""Модуль для работы с логами поиска в MongoDB.
Содержит функции для записи логов и получения статистики.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from mongo_client import coll

def log_search(search_type, params, results_count):
    """Записывает информацию о поисковом запросе в MongoDB.
    Параметры:
        search_type: Тип поиска ('keyword', 'genre_year')
        params: Параметры поиска (dict)
        results_count: Количество найденных результатов
    """
    try:
        if isinstance(params, dict):
            params_clean = dict(params)
            params_clean.pop("offset", None)
        else:
            params_clean = params
    except Exception:
        params_clean = params

    ts = datetime.now(ZoneInfo("Europe/Berlin")).replace(microsecond=0)
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")

    doc = {
        "timestamp": ts_str,
        "search_type": search_type,
        "params": params_clean,
        "results_count": results_count,
    }
    
    if coll is None:
        print("Инфо: MongoDB недоступна — пропускаю логирование.")
        return

    coll.insert_one(doc)


def get_top_queries(limit=5):
    """Возвращает топ самых популярных запросов.
    Параметры:
        limit: Максимальное количество запросов
    Возвращает:
        list: Список словарей с агрегированной статистикой
    """
    if coll is None:
        return []

    pipeline = [
        {
            "$group": {
                "_id": {"type": "$search_type", "params": "$params"},
                "count": {"$sum": 1},
                "last": {"$max": "$timestamp"},
            }
        },
        {"$sort": {"count": -1, "last": -1}},
        {"$limit": limit},
    ]
    return list(coll.aggregate(pipeline))


def get_last_queries(limit=5):
    """Возвращает последние уникальные выполненные запросы.
    Параметры:
        limit: Максимальное количество запросов
    Возвращает:
        list: Список последних уникальных запросов, отсортированных по времени
    """
    if coll is None:
        return []
    
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {
            "$group": {
                "_id": {"type": "$search_type", "params": "$params"},
                "timestamp": {"$first": "$timestamp"},
                "search_type": {"$first": "$search_type"},
                "params": {"$first": "$params"},
                "results_count": {"$first": "$results_count"},
            }
        },
        {"$sort": {"timestamp": -1}},
        {"$limit": limit},
    ]
    return list(coll.aggregate(pipeline))


def clear_logs():
    """Удаляет все документы с логами поисковых запросов из коллекции. 
    Параметры:
        int: Число удалённых документов
    """
    if coll is None:
        return 0
    result = coll.delete_many({})
    return result.deleted_count
