# === log_writer.py ===
from datetime import datetime, timezone
from mongo_client import coll


def _clean_params(params):
    """Подготовить объект `params` для сохранения в логе.

    Убираем технические поля, не влияющие на смысл запроса (например, `offset`).
    Возвращаем копию словаря с допустимыми ключами или оригинал, если не словарь.
    """
    if not isinstance(params, dict):
        return params
    p = dict(params)
    p.pop("offset", None)
    return p


def log_search(search_type, params, results_count):
    """Записать информацию о поисковом запросе в MongoDB.

    Формат документа в Mongo должен быть:
    {
      "timestamp": "YYYY-MM-DDTHH:MM:SS",
      "search_type": "keyword",
      "params": { ... },
      "results_count": 3
    }

    `timestamp` сохраняется в виде строки ISO (без микросекунд и смещения).
    """
    try:
        params_clean = _clean_params(params)
    except Exception:
        params_clean = params

    # Форматируем timestamp как строку ISO без микросекунд
    ts = datetime.now(timezone.utc).astimezone(timezone.utc).replace(microsecond=0)
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")

    doc = {
        "timestamp": ts_str,
        "search_type": search_type,
        "params": params_clean,
        "results_count": results_count,
    }

    # Вставка документа в общую коллекцию (в mongo_client.coll)
    coll.insert_one(doc)
