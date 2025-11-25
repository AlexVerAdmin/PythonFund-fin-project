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
    get_films_by_actor,
    get_films_by_actor_count,
    get_ratings,
)
from log_writer import log_search
from log_stats import get_top_queries, get_last_queries, clear_logs
from formatter import (
    print_movies_table,
    print_genres,
    print_stats,
    print_actors,
    SEPARATOR,
)
from config import LIMIT, RATING_DESCRIPTIONS


def _ask_yes(prompt):
    r = input(prompt).strip().lower()
    # Accept English 'y'/'yes' and Russian 'д'/'да'
    return r in ("y", "yes", "д", "да")


def handle_actor_films(actor_id, actor_name):
    """Показать все фильмы с участием выбранного актёра.
    
    Args:
        actor_id: ID актёра в базе данных
        actor_name: Полное имя актёра для отображения
    """
    print("\n" + "=" * 70)
    print(f"🎬 ФИЛЬМЫ С УЧАСТИЕМ: {actor_name}".center(70))
    print("=" * 70 + "\n")
    
    # Получаем общее количество фильмов
    try:
        total = get_films_by_actor_count(actor_id)
        print(f"📊 Всего фильмов с участием актёра: {total}\n")
    except Exception:
        total = None
    
    offset = 0
    while True:
        films = get_films_by_actor(actor_id, offset=offset, limit=LIMIT)
        
        if not films:
            print("\n  ℹ️  Фильмы не найдены\n")
            break
        
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"=== Показаны {start}–{end} из {total} ===\n")
        
        print_movies_table(films, offset=offset, total=total, show_header=False)
        print(SEPARATOR)
        
        # Если это последняя страница, выходим
        if len(films) < LIMIT:
            break
        
        if not _ask_yes("\n📄 Показать следующие 10 фильмов? (y/n): "):
            break
        
        offset += LIMIT
    
    print()


def handle_keyword_search():
    """Интерактивный поиск по ключевому слову с поддержкой пагинации.

    Запрашивает у пользователя ключевое слово, выводит результаты по
    страницам и логирует каждый просмотр страницы в MongoDB.
    """
    print("\n" + "=" * 60)
    print("🔍 ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ".center(60))
    print("=" * 60 + "\n")
    
    # Сбор критериев поиска (сначала формируем запрос, затем выполняем и логируем)
    keyword = input("➤ Введите ключевое слово (или Enter для отмены): ").strip()
    if not keyword:
        print("\n🔙 Ключевое слово не задано, возвращаюсь в меню.\n")
        return

    # Опциональный жанр
    genre_id = None
    if _ask_yes("\n🎭 Фильтровать по жанру? (y/n): "):
        genres = get_genres()
        if not genres:
            print("\n⚠️  Список жанров пуст, фильтр по жанру пропущен.\n")
        else:
            print_genres(genres)
            try:
                idx = int(input("➤ Выберите номер жанра (или Enter для отмены): ").strip())
                if 1 <= idx <= len(genres):
                    genre_id = genres[idx - 1].get("category_id")
                    print(f"\n✅ Выбран жанр: {genres[idx - 1].get('name')}\n")
                else:
                    print("\n⚠️  Неверный номер жанра, фильтр пропущен.\n")
            except Exception:
                print("\n🔙 Фильтр по жанру пропущен.\n")

    # Опциональные года
    year_min = year_max = None
    try:
        min_year, max_year = get_year_bounds()
        print(f"\n📅 Доступные годы: {min_year} — {max_year}")
        lower = input(f"➤ Нижний год (Enter для {min_year}): ").strip()
        upper = input(f"➤ Верхний год (Enter для {max_year}): ").strip()
        if lower or upper:
            y1 = int(lower) if lower else int(min_year)
            y2 = int(upper) if upper else int(max_year)
            if y1 <= y2:
                year_min, year_max = y1, y2
                print(f"\n✅ Диапазон лет: {y1}–{y2}\n")
            else:
                print("\n⚠️  Неправильный диапазон лет, фильтр по годам пропущен.\n")
    except Exception:
        # Если не удалось получить границы — пропускаем
        year_min = year_max = None

    # Опциональный рейтинг
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("\n⭐ Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                desc = RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"  {i}. {r} — {desc}")
            r_choice = input("\n➤ Выберите номер рейтинга (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    rating = ratings[ri - 1]
                    print(f"\n✅ Выбран рейтинг: {rating}\n")
                else:
                    print("\n⚠️  Неверный выбор рейтинга, пропускаю фильтр.\n")
    except Exception:
        rating = None

    # Подсчёт общего числа совпадений по сформированному запросу
    try:
        total = get_keyword_count(keyword, genre_id=genre_id, year_min=year_min, year_max=year_max, rating=rating)
        print(f"\n📊 Найдено всего: {total} фильм(ов)\n")
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
        # После показа страницы — позволяеm выбрать один или несколько фильмов подряд
        # Если пользователь сразу нажимает Enter (пустой ввод) — переходим дальше.
        # На последней странице выбор также доступен, но после него мы вернёмся в меню.
        user_pressed_enter = False
        while True:
            choice = input("Введите номер фильма для просмотра актёров (Enter — продолжить): ").strip()
            if not choice:
                user_pressed_enter = True
                break
            try:
                idx = int(choice)
                # индекс в returned `films` вычисляется относительно offset
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))
                    
                    # Предложить выбрать актёра для просмотра его фильмов
                    if actors and _ask_yes("\n🎭 Хотите посмотреть фильмы одного из актёров? (y/n): "):
                        while True:
                            actor_choice = input(f"\n➤ Введите номер актёра (1-{len(actors)}) или Enter для отмены: ").strip()
                            if not actor_choice:
                                break
                            try:
                                actor_idx = int(actor_choice)
                                if 1 <= actor_idx <= len(actors):
                                    selected_actor = actors[actor_idx - 1]
                                    actor_id = selected_actor.get('actor_id')
                                    fn = selected_actor.get('first_name', '').strip().title()
                                    ln = selected_actor.get('last_name', '').strip().title()
                                    actor_name = f"{fn} {ln}"
                                    handle_actor_films(actor_id, actor_name)
                                    break
                                else:
                                    print(f"❌ Неверный номер — введите число от 1 до {len(actors)}")
                            except ValueError:
                                print("❌ Ожидался номер актёра.")
                else:
                    print(f"Неверный номер — введите число от {offset + 1} до {offset + len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        # Если это была последняя страница, не спрашиваем про следующую — возвращаемся в меню
        if len(films) < LIMIT:
            break
        if user_pressed_enter:
            # Пользователь нажал Enter — перейти к следующей странице
            offset += LIMIT
            continue
        if not _ask_yes("Показать следующие 10 результатов? (y/n): "):
            break
        offset += LIMIT


def handle_genre_search():
    """Поиск фильмов по жанру и диапазону лет (интерактивный режим).

    Пользователь выбирает жанр из списка и задаёт границы годов. Результаты
    показываются по страницам и логируются.
    """
    print("\n" + "=" * 60)
    print("🎭 ПОИСК ПО ЖАНРУ И ГОДАМ".center(60))
    print("=" * 60 + "\n")
    
    # Загрузка списка жанров из БД
    genres = get_genres()
    if not genres:
        print("⚠️  Список жанров пуст.\n")
        return
    print_genres(genres)
    try:
        idx = int(input("➤ Выберите номер жанра: ").strip())
        if not 1 <= idx <= len(genres):
            print("\n❌ Неверный выбор\n")
            return
    except ValueError:
        print("\n❌ Неверный ввод\n")
        return
    genre = genres[idx - 1]
    print(f"\n✅ Выбран жанр: {genre.get('name')}\n")
    
    min_year, max_year = get_year_bounds()
    print(f"📅 Доступные годы: {min_year} — {max_year}")
    lower = input(f"➤ Нижний год (или Enter для {min_year}): ").strip()
    upper = input(f"➤ Верхний год (или Enter для {max_year}): ").strip()
    try:
        y1 = int(lower) if lower else int(min_year)
        y2 = int(upper) if upper else int(max_year)
    except ValueError:
        print("\n❌ Неверный формат года\n")
        return
    if y1 > y2:
        print("\n❌ Нижний год больше верхнего\n")
        return
    print(f"\n✅ Диапазон лет: {y1}–{y2}\n")

    # Опциональный рейтинг для жанра-поиска
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                desc = RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"{i}. {r} — {desc}")
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
        print(f"📊 Найдено всего: {total} фильм(ов)\n")
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
        # После показа страницы — позволяем выбрать несколько фильмов подряд для просмотра актёров
        # Если пользователь сразу нажимает Enter (пустой ввод) — переходим дальше.
        # На последней странице выбор также доступен, но после него мы вернёмся в меню.
        user_pressed_enter = False
        while True:
            choice = input("Введите номер фильма для просмотра актёров (Enter — продолжить): ").strip()
            if not choice:
                user_pressed_enter = True
                break
            try:
                idx = int(choice)
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))
                    
                    # Предложить выбрать актёра для просмотра его фильмов
                    if actors and _ask_yes("\n🎭 Хотите посмотреть фильмы одного из актёров? (y/n): "):
                        while True:
                            actor_choice = input(f"\n➤ Введите номер актёра (1-{len(actors)}) или Enter для отмены: ").strip()
                            if not actor_choice:
                                break
                            try:
                                actor_idx = int(actor_choice)
                                if 1 <= actor_idx <= len(actors):
                                    selected_actor = actors[actor_idx - 1]
                                    actor_id = selected_actor.get('actor_id')
                                    fn = selected_actor.get('first_name', '').strip().title()
                                    ln = selected_actor.get('last_name', '').strip().title()
                                    actor_name = f"{fn} {ln}"
                                    handle_actor_films(actor_id, actor_name)
                                    break
                                else:
                                    print(f"❌ Неверный номер — введите число от 1 до {len(actors)}")
                            except ValueError:
                                print("❌ Ожидался номер актёра.")
                else:
                    print(f"Неверный номер — введите число от {offset + 1} до {offset + len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        # Если это была последняя страница, не спрашиваем про следующую — возвращаемся в меню
        if len(films) < LIMIT:
            break
        if user_pressed_enter:
            offset += LIMIT
            continue
        if not _ask_yes("Показать следующие 10 результатов? (y/n): "):
            break
        offset += LIMIT


def main():
    """Главное меню приложения с интерактивным управлением."""
    print("\n" + "🎬" * 30)
    print("ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ ПОИСКА ФИЛЬМОВ".center(60))
    print("База данных: Sakila".center(60))
    print("🎬" * 30 + "\n")
    
    while True:
        print("=" * 60)
        print("📋 ГЛАВНОЕ МЕНЮ".center(60))
        print("=" * 60)
        print("  1. 🔍 Поиск по ключевому слову")
        print("  2. 🎭 Поиск по жанру и диапазону лет")
        print("  3. 📊 Показать статистику запросов")
        print("  4. 🗑️  Очистить логи MongoDB")
        print("  q. 🚪 Выход")
        print("=" * 60)

        choice = input("\n➤ Выберите опцию: ").strip()

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
            if _ask_yes("\n⚠️  Это удалит ВСЕ сохранённые запросы в MongoDB. Продолжить? (y/n): "):
                try:
                    deleted = clear_logs()
                    print(f"\n✅ Удалено документов: {deleted}")
                    print(SEPARATOR)
                except Exception as exc:
                    print(f"\n❌ Не удалось очистить логи: {exc}")
            else:
                print("\n🔙 Операция отменена.")
                print(SEPARATOR)

        elif choice in ["q", "quit", "exit", "Q"]:
            print("\n" + "=" * 60)
            print("👋 До встречи!".center(60))
            print("=" * 60 + "\n")
            break

        else:
            print("\n❌ Неверная опция. Пожалуйста, выберите 1-4 или q.\n")


if __name__ == "__main__":
    main()