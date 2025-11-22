# === log_writer.py ===
from datetime import datetime, timezone
from mongo_client import coll


def log_search(search_type, params, results_count):
    """Записать информацию о поисковом запросе в MongoDB.

    Сохраняются исходные `params` и очищённые `user_params`, из которых
    убираются временные поля (например, `offset`) — это нужно, чтобы
    похожие по смыслу запросы группировались в статистике.

    `timestamp` хранится как объект `datetime` (UTC) для корректной сортировки.
    """
    # Подготовка параметров для группировки (убираем пагинацию)
    user_params = None
    try:
        if isinstance(params, dict):
            user_params = dict(params)
            user_params.pop("offset", None)
        else:
            user_params = params
    except Exception:
        # Если копирование упало, сохраняем оригинал
        user_params = params

    doc = {
        "timestamp": datetime.now(timezone.utc),
        "search_type": search_type,
        "params": params,
        "user_params": user_params,
        "results_count": results_count,
    }

    # Вставка документа в общую коллекцию (в mongo_client.coll)
    coll.insert_one(doc)
