# === log_stats.py ===
from mongo_client import coll


def get_top_queries(limit=5):
    if not coll:
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
    if not coll:
        return []
    return list(coll.find().sort("timestamp", -1).limit(limit))


def clear_logs():
    """
    Удаляет все документы с логами поисковых запросов из коллекции.
    Возвращает число удалённых документов.
    """
    if not coll:
        return 0
    result = coll.delete_many({})
    return result.deleted_count