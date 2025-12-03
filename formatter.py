"""
Здесь собраны функции вывода результатов поиска, списков жанров,
диапазонов лет и статистики.
"""

from config import AGE_RATING_DESCRIPTIONS
from favorites import is_favorite

# Визуальный разделитель, печатаемый после блока результатов
SEPARATOR = "*" * 100
SEPARATOR_MINUS = "-" * 100
SEPARATOR_EQUAL = "=" * 70


def print_movies_table(films, offset=0, total=None, show_header=True):
    """
    Выводит список фильмов в табличном формате.
    """
    if not films:
        print("\n   Фильмы не найдены\n")
        return

    if show_header:
        # print("\n" + "=" * 100)
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"{f' РЕЗУЛЬТАТЫ ПОИСКА (Показаны {start}–{end} из {total})':^100}")
        else:
            # Центрирование 
            print(f"{' РЕЗУЛЬТАТЫ ПОИСКА':^100}")
        # print("=" * 100)

    for i, film in enumerate(films, start=offset + 1):
        title = film.get("title", "Без названия")
        year = film.get("release_year", "N/A")
        ren_raw = film.get("rental_rate")
        rep_raw = film.get("replacement_cost")

        try:
            # Форматируем цены до двух знаков после запятой
            # если_истина if условие else если_ложь
            ren = f"{float(ren_raw):.2f}" if ren_raw is not None else "N/A" 
        except Exception:
            ren = str(ren_raw) if ren_raw is not None else "N/A"
        try:
            rep = f"{float(rep_raw):.2f}" if rep_raw is not None else "N/A"
        except Exception:
            rep = str(rep_raw) if rep_raw is not None else "N/A"
        rating = film.get("rating", "N/A")

        # Подставляем описание возрастной категории из конфига; если описания нет —
        # оставляем код
        rating_desc = AGE_RATING_DESCRIPTIONS.get(rating, rating)
        desc = film.get("description") or ""

        # Проверяем, находится ли фильм в избранном
        film_id = film.get("film_id")
        fav_marker = " " * 10 + "❤" if film_id and is_favorite(film_id) else ""  # favorites.py

        # Форматируем вывод с разделителем между фильмами
        print(f"\n  {i}.   {title} ({year}){fav_marker}")
        print(f"   Аренда: ${ren} | Покупка: ${rep} | Возрастной рейтинг: {rating_desc}")

        if desc:
            # Ограничиваем длину описания для лучшей читаемости
            desc_lines = desc[:200] + "..." if len(desc) > 200 else desc
            print(f"       {desc_lines}")


def print_genres(genres):
    """
    Выводит список жанров с индексами для выбора пользователем.
    """
    if not genres:
        print("\n    Жанры не найдены в базе.\n")
        return

    # print("\n" + "=" * 60)
    print(f"{' ДОСТУПНЫЕ ЖАНРЫ':^60}")
    # print("=" * 60)

    # Выводим жанры для выбора пользователем
    for idx, g in enumerate(genres, start=1):
        name = g.get('name', 'Неизвестно')
        print(f"  {idx:2d}. {name}")
    print(SEPARATOR_EQUAL + "\n")


def _format_search_params(params):
    """
    Форматирует параметры поиска в читаемую строку.
    """
    if not params:
        return "нет параметров"

    parts = []
    if "keyword" in params:
        parts.append(f"ключевое слово: '{params['keyword']}'")
    if "genre_id" in params:
        parts.append(f"жанр ID: {params['genre_id']}")
    if "year_min" in params and "year_max" in params:
        parts.append(f"годы: {params['year_min']}–{params['year_max']}")
    if "age_rating" in params:
        parts.append(f"возрастная категория: {params['age_rating']}")

    return ", ".join(parts) if parts else str(params)


def print_stats(top_queries, last_queries):
    """
    Выводит статистику популярных и последних запросов из MongoDB.
    """
    # print("\n" + "=" * 80)
    print(f"\n{' ПОПУЛЯРНЫЕ ЗАПРОСЫ':^80}")
    # print("=" * 80)

    if not top_queries:
        print("  Статистика недоступна (нет сохранённых запросов).\n")
    else:
        for idx, item in enumerate(top_queries, 1):
            _id = item.get("_id", {})
            count = item.get("count", 0)
            last = item.get("last", "неизвестно")
            search_type = _id.get("type", "неизвестный тип")
            params = _id.get("params", {})

            # Преобразуем тип поиска в читаемый формат
            type_name = {
                "keyword": "Поиск по ключевому слову",
                "genre_year": "Поиск по жанру и годам"
            }.get(search_type, search_type)

            print(f"\n  {idx}. {type_name}")
            print(f"     Параметры: {_format_search_params(params)}")
            print(f"     Количество запросов: {count}")
            print(f"     Последний запрос: {last}")

    # print("\n" + "=" * 80)
    print(f"\n{' НЕДАВНИЕ ЗАПРОСЫ':^80}")
    # print("=" * 80)

    if not last_queries:
        print("  Недавних запросов нет.\n")
    else:
        for idx, q in enumerate(last_queries, 1):
            timestamp = q.get("timestamp", "неизвестно")
            search_type = q.get("search_type", "неизвестный тип")
            params = q.get("params", {})
            results_count = q.get("results_count", 0)

            # Преобразуем тип поиска в читаемый формат
            type_name = {
                "keyword": "Поиск по ключевому слову",
                "genre_year": "Поиск по жанру и годам"
            }.get(search_type, search_type)

            print(f"\n  {idx}. [{timestamp}] {type_name}")
            print(f"     Параметры: {_format_search_params(params)}")
            print(f"     Найдено результатов: {results_count}")

    print(SEPARATOR_EQUAL + "\n")


def print_actors(actors, film_title=None):
    """
    Выводит список актёров для выбранного фильма.
    """
    print("\n" + SEPARATOR_EQUAL)
    if film_title:
        print(f"{f' АКТЁРЫ ФИЛЬМА: {film_title}':^70}")
    else:
        print(f"{' СПИСОК АКТЁРОВ':^70}")
    print(SEPARATOR_EQUAL)

    if not actors:
        print("\n    Актёры не найдены.\n")
    else:
        for idx, a in enumerate(actors, 1):
            fn = (a.get('first_name') or '').strip().title()
            ln = (a.get('last_name') or '').strip().title()
            print(f"  {idx:2d}. {fn} {ln}")

    print(SEPARATOR_EQUAL + "\n")
