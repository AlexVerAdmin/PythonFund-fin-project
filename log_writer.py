# === log_writer.py ===
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from mongo_client import coll


def log_search(search_type, params, results_count):
    """Записывает информацию о поисковом запросе в MongoDB.
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
    # Если Mongo не доступен — пропускаем логирование и информируем
    if not coll:
        # Одноразовое информирование оставим на усмотрение: здесь выводим краткое сообщение
        print("Инфо: MongoDB недоступна — пропускаю логирование.")
        return

    # Вставка документа в общую коллекцию
    coll.insert_one(doc)
