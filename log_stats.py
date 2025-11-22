# === log_stats.py ===
from mongo_client import coll


def get_top_queries(limit=5):
    pipeline = [
        {
            "$group": {
                "_id": {"type": "$search_type", "params": "$user_params"},
                "count": {"$sum": 1},
                "last": {"$max": "$timestamp"},
            }
        },
        {"$sort": {"count": -1, "last": -1}},
        {"$limit": limit},
    ]
    return list(coll.aggregate(pipeline))


def get_last_queries(limit=5):
    return list(coll.find().sort("timestamp", -1).limit(limit))


def clear_logs():
    """Удалить все документы с логами поисковых запросов из коллекции.

    Возвращает число удалённых документов.
    """
    result = coll.delete_many({})
    return result.deleted_count


def _format_agg_item(item):
    """Вспомогательная функция для форматирования агрегированных записей.

    Используется в `formatter.print_stats` при необходимости; оставлена
    для локального форматирования результатов агрегирования.
    """
    _id = item.get("_id", {})
    return {
        "type": _id.get("type"),
        "params": _id.get("params"),
        "count": item.get("count"),
        "last": item.get("last"),
    }