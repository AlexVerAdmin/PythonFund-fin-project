"""Консольное интерактивное приложение для поиска фильмов.

Модуль содержит текстовое меню и обработчики для поиска фильмов по базе
Sakila. Используются функции из `mysql_connector` для SQL-запросов,
`log_writer` для записи логов в MongoDB и `log_stats`/`formatter` для
форматирования и вывода статистики.

Основные функции:
- `handle_keyword_search` — поиск по ключевому слову с пагинацией.
- `handle_genre_search` — поиск по жанру и диапазону лет.
- `main` — цикл главного меню приложения.
"""

from mysql_connector import (
    search_by_keyword,
    search_by_genre_and_year,
    get_genres,
    get_year_bounds,
    get_keyword_count,
    get_genre_year_count,
    get_actors_by_film,
    get_ratings,
)
from log_writer import log_search
from log_stats import get_top_queries, get_last_queries, clear_logs
from formatter import (
    print_movies_table,
    print_genres,
    print_year_bounds,
    print_stats,
    print_actors,
    SEPARATOR,
)
from config import LIMIT


def _ask_yes(prompt):
    r = input(prompt).strip().lower()
    # Accept English 'y'/'yes' and Russian 'д'/'да'
    return r in ("y", "yes", "д", "да")


def handle_keyword_search():
    """Интерактивный поиск по ключевому слову с поддержкой пагинации.

    Запрашивает у пользователя ключевое слово, выводит результаты по
    страницам и логирует каждый просмотр страницы в MongoDB.
    """
    # Сбор критериев поиска (сначала формируем запрос, затем выполняем и логируем)
    keyword = input("Введите ключевое слово (или Enter для пропуска): ").strip()
    if not keyword:
        print("Ключевое слово не задано, возвращаюсь в меню.")
        return

    # Опциональный жанр
    genre_id = None
    if _ask_yes("Фильтровать по жанру? (y/n): "):
        genres = get_genres()
        if not genres:
            print("Список жанров пуст, фильтр по жанру пропущен.")
        else:
            print_genres(genres)
            try:
                idx = int(input("Выберите номер жанра (или Enter для отмены): ").strip())
                if 1 <= idx <= len(genres):
                    genre_id = genres[idx - 1].get("category_id")
                else:
                    print("Неверный номер жанра, фильтр пропущен.")
            except Exception:
                print("Фильтр по жанру пропущен.")

    # Опциональные года
    year_min = year_max = None
    try:
        min_year, max_year = get_year_bounds()
        print_year_bounds(min_year, max_year)
        lower = input(f"Нижний год (Enter для {min_year}): ").strip()
        upper = input(f"Верхний год (Enter для {max_year}): ").strip()
        if lower or upper:
            y1 = int(lower) if lower else int(min_year)
            y2 = int(upper) if upper else int(max_year)
            if y1 <= y2:
                year_min, year_max = y1, y2
            else:
                print("Неправильный диапазон лет, фильтр по годам пропущен.")
    except Exception:
        # Если не удалось получить границы — пропускаем
        year_min = year_max = None

    # Опциональный рейтинг
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                print(f"{i}. {r}")
            r_choice = input("Выберите номер рейтинга (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    rating = ratings[ri - 1]
                else:
                    print("Неверный выбор рейтинга, пропускаю фильтр.")
    except Exception:
        rating = None

    # Подсчёт общего числа совпадений по сформированному запросу
    try:
        total = get_keyword_count(keyword, genre_id=genre_id, year_min=year_min, year_max=year_max, rating=rating)
        print(f"Найдено всего: {total}")
    except Exception:
        total = None

    # Логируем сам запрос ОДИН раз (без offset)
    params = {"keyword": keyword}
    if genre_id is not None:
        params["genre_id"] = genre_id
    if year_min is not None and year_max is not None:
        params.update({"year_min": year_min, "year_max": year_max})
    if rating:
        params["rating"] = rating
    try:
        # Если total известен, логируем его как результаты, иначе 0
        log_search("keyword", params, int(total) if total is not None else 0)
    except Exception:
        # Не критично, продолжаем без прерывания
        pass

    # Постраничный вывод — без логирования каждой страницы
    offset = 0
    while True:
        films = search_by_keyword(keyword, offset=offset, limit=LIMIT, genre_id=genre_id, year_min=year_min, year_max=year_max, rating=rating)
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"=== Результаты (Показаны {start}–{end} из {total}) ===")
            print_movies_table(films, offset=offset, total=total, show_header=False)
            print(SEPARATOR)
        else:
            print_movies_table(films, offset=offset, total=total)
            print(SEPARATOR)
        # После показа страницы — позволяем пользователю выбрать фильм для просмотра актёров
        choice = input("Введите номер фильма для просмотра актёров (или Enter чтобы продолжить): ").strip()
        if choice:
            try:
                idx = int(choice)
                # индекс в returned `films` вычисляется относительно offset
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))
                else:
                    print(f"Неверный номер — введите число от {offset + 1} до {offset + len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        if len(films) < LIMIT:
            break
        if not _ask_yes("Показать следующие 10 результатов? (y/n): "):
            break
        offset += LIMIT


def handle_genre_search():
    """Поиск фильмов по жанру и диапазону лет (интерактивный режим).

    Пользователь выбирает жанр из списка и задаёт границы годов. Результаты
    показываются по страницам и логируются.
    """
    # Загрузка списка жанров из БД
    genres = get_genres()
    if not genres:
        print("Список жанров пуст.")
        return
    print_genres(genres)
    try:
        idx = int(input("Выберите номер жанра: ").strip())
        if not 1 <= idx <= len(genres):
            print("Неверный выбор")
            return
    except ValueError:
        print("Неверный ввод")
        return
    genre = genres[idx - 1]
    min_year, max_year = get_year_bounds()
    print_year_bounds(min_year, max_year)
    lower = input(f"Нижний год (или Enter для {min_year}): ").strip()
    upper = input(f"Верхний год (или Enter для {max_year}): ").strip()
    try:
        y1 = int(lower) if lower else int(min_year)
        y2 = int(upper) if upper else int(max_year)
    except ValueError:
        print("Неверный формат года")
        return
    if y1 > y2:
        print("Нижний год больше верхнего")
        return

    # Опциональный рейтинг для жанра-поиска
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                print(f"{i}. {r}")
            r_choice = input("Выберите номер рейтинга (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    rating = ratings[ri - 1]
                else:
                    print("Неверный выбор рейтинга, пропускаю фильтр.")
    except Exception:
        rating = None

    # Показать общее количество совпадений перед пагинацией
    try:
        total = get_genre_year_count(genre.get("category_id"), y1, y2, rating=rating)
        print(f"Найдено всего: {total}")
    except Exception:
        total = None

    # Логируем сформированный запрос ОДИН раз (без offset)
    params = {"genre_id": genre.get("category_id"), "year_min": y1, "year_max": y2}
    if rating:
        params["rating"] = rating
    try:
        log_search("genre_year", params, int(total) if total is not None else 0)
    except Exception:
        pass

    offset = 0
    while True:
        films = search_by_genre_and_year(genre["category_id"], y1, y2, offset=offset, limit=LIMIT, rating=rating)
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"=== Результаты (Показаны {start}–{end} из {total}) ===")
            print_movies_table(films, offset=offset, total=total, show_header=False)
            print(SEPARATOR)
        else:
            print_movies_table(films, offset=offset, total=total)
            print(SEPARATOR)
        # Выбор фильма для просмотра актёров на текущей странице
        choice = input("Введите номер фильма для просмотра актёров (или Enter чтобы продолжить): ").strip()
        if choice:
            try:
                idx = int(choice)
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))
                else:
                    print(f"Неверный номер — введите число от {offset + 1} до {offset + len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        if len(films) < LIMIT:
            break
        if not _ask_yes("Показать следующие 10 результатов? (y/n): "):
            break
        offset += LIMIT


def main():
    while True:
        print("=== Поиск фильмов ===")
        print("1. Поиск по ключевому слову")
        print("2. Поиск по жанру и диапазону лет")
        print("3. Показать статистику")
        print("4. Очистить логи MongoDB")
        print("5. Выход")

        choice = input("Выберите опцию: ").strip()

        if choice == "1":
            handle_keyword_search()

        elif choice == "2":
            handle_genre_search()

        elif choice == "3":
            top_q = get_top_queries()
            last_q = get_last_queries()
            print_stats(top_q, last_q)
            print(SEPARATOR)

        elif choice == "4":
            if _ask_yes("Это удалит ВСЕ сохранённые запросы в MongoDB. Продолжить? (y/n): "):
                try:
                    deleted = clear_logs()
                    print(f"Удалено документов: {deleted}")
                    print(SEPARATOR)
                except Exception as exc:
                    print(f"Не удалось очистить логи: {exc}")
            else:
                print("Операция отменена.")
                print(SEPARATOR)

        elif choice == "5":
            print("До встречи!")
            break

        else:
            print("Неверная опция")


if __name__ == "__main__":
    main()