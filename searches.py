"""Модуль для интерактивных функций поиска фильмов.

Содержит обработчики для поиска по ключевому слову, по жанру и годам,
а также для просмотра фильмов актёра с поддержкой пагинации.
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
from log_stats import log_search
from formatter import (
    print_movies_table,
    print_genres,
    print_actors,
    SEPARATOR,
    SEPARATOR_MINUS,
    SEPARATOR_EQUAL
)
from config import LIMIT, RATING_DESCRIPTIONS
from input_utils import process_yes_no_input, process_input, convert_layout_to_english
from favorites import add_to_favorites


def handle_actor_films(actor_id, actor_name):
    """Показать все фильмы с участием выбранного актёра.

    Args:
        actor_id: ID актёра в базе данных
        actor_name: Полное имя актёра для отображения
    """
    print("\n" + "=" * 70)
    print(f"{f' ФИЛЬМЫ С УЧАСТИЕМ: {actor_name}':^70}")
    print("=" * 70 + "\n")

    # Получаем общее количество фильмов
    try:
        total = get_films_by_actor_count(actor_id)
        print(f" Всего фильмов с участием актёра: {total}\n")
    except Exception:
        total = None

    offset = 0
    while True:
        films = get_films_by_actor(actor_id, offset=offset, limit=LIMIT)

        if not films:
            print("\n   Фильмы не найдены\n")
            break

        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"{SEPARATOR_MINUS}\n")

        print_movies_table(
            films,
            offset=offset,
            total=total,
            show_header=False)
        print(SEPARATOR)

        # Если это последняя страница, выходим
        if len(films) < LIMIT:
            break

        if total is not None:
            prompt = f"\n {start}–{end} из {total}. Нажмите Enter для продолжения, 'f<номер>' для добавления в избранное или 'q' для выхода: "
        else:
            prompt = "\n Нажмите Enter для продолжения, 'f<номер>' для добавления в избранное или 'q' для выхода: "
        choice = process_input(prompt).lower()
        if choice in ('q', 'quit', 'exit', 'esc'):
            break
        
        # Обработка команды добавления в избранное
        if choice.startswith('f'):
            try:
                # Конвертируем возможную неправильную раскладку (а123 -> f123)
                converted_choice = convert_layout_to_english(choice)
                film_num = int(converted_choice[1:])
                if 1 <= film_num <= len(films):
                    film = films[film_num - 1]
                    add_to_favorites(
                        film.get('film_id'),
                        film.get('title'),
                        film.get('release_year'),
                        film.get('rating')
                    )
                    print(f" ⭐ Фильм '{film.get('title')}' добавлен в избранное!")
                else:
                    print(f" ⚠️  Неверный номер фильма (доступно: 1-{len(films)})")
            except (ValueError, IndexError):
                print(" ⚠️  Неверный формат. Используйте: f<номер> (например, f3)")
            continue

        offset += LIMIT

    print()


def handle_keyword_search():
    """Интерактивный поиск по ключевому слову с поддержкой пагинации.

    Запрашивает у пользователя ключевое слово, выводит результаты по
    страницам и логирует каждый просмотр страницы в MongoDB.
    """
    print("\n" + SEPARATOR_EQUAL)
    print(f"{' ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ':^60}")
    print(SEPARATOR_EQUAL + "\n")

    # Сбор критериев поиска (сначала формируем запрос, затем выполняем и
    # логируем)
    keyword = process_input(
        " Введите ключевое слово (или Enter для отмены): ")
    if not keyword:
        print("\n Ключевое слово не задано, возвращаюсь в меню.\n")
        return

    # Опциональный жанр
    genre_id = None
    if process_yes_no_input("\n Фильтровать по жанру? (y/n): "):
        genres = get_genres()
        if not genres:
            print("\n  Список жанров пуст, фильтр по жанру пропущен.\n")
        else:
            print_genres(genres)
            try:
                idx = int(
                    input(" Выберите номер жанра (или Enter для отмены): ").strip())
                if 1 <= idx <= len(genres):
                    genre_id = genres[idx - 1].get("category_id")
                    print(f"\n Выбран жанр: {genres[idx - 1].get('name')}\n")
                else:
                    print("\n  Неверный номер жанра, фильтр пропущен.\n")
            except Exception:
                print("\n Фильтр по жанру пропущен.\n")

    # Опциональные года
    year_min = year_max = None
    try:
        min_year, max_year = get_year_bounds()
        print(f"\n Доступные годы: {min_year} — {max_year}")
        lower = input(f" Нижний год (Enter для {min_year}): ").strip()
        upper = input(f" Верхний год (Enter для {max_year}): ").strip()
        if lower or upper:
            y1 = int(lower) if lower else int(min_year)
            y2 = int(upper) if upper else int(max_year)
            if y1 <= y2:
                year_min, year_max = y1, y2
                print(f"\n Диапазон лет: {y1}–{y2}\n")
            else:
                print("\n  Неправильный диапазон лет, фильтр по годам пропущен.\n")
    except Exception:
        # Если не удалось получить границы — пропускаем
        year_min = year_max = None

    # Опциональный рейтинг
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("\n Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                desc = RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"  {i}. {r} — {desc}")
            r_choice = input(
                "\n Выберите номер рейтинга (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    rating = ratings[ri - 1]
                    print(f"\n Выбран рейтинг: {rating}\n")
                else:
                    print("\n  Неверный выбор рейтинга, пропускаю фильтр.\n")
    except Exception:
        rating = None

    # Подсчёт общего числа совпадений по сформированному запросу
    try:
        total = get_keyword_count(
            keyword,
            genre_id=genre_id,
            year_min=year_min,
            year_max=year_max,
            rating=rating)
        print(f"\n\n Найдено всего: {total} фильм(ов)\n")
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

    # Постраничный вывод результатов
    offset = 0
    while True:
        films = search_by_keyword(
            keyword,
            offset=offset,
            limit=LIMIT,
            genre_id=genre_id,
            year_min=year_min,
            year_max=year_max,
            rating=rating)
        # Если результатов нет на первой странице — возвращаемся в меню
        if not films and offset == 0:
            print("\n   Фильмы не найдены\n")
            break
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"{SEPARATOR_MINUS}\n")
            print_movies_table(
                films,
                offset=offset,
                total=total,
                show_header=False)
            print(SEPARATOR)
        else:
            print_movies_table(films, offset=offset, total=total)
            print(SEPARATOR)
        # После показа страницы — позволяеm выбрать один или несколько фильмов подряд
        # Если пользователь сразу нажимает Enter (пустой ввод) — переходим дальше.
        # На последней странице выбор также доступен, но после него мы вернёмся в меню.
        user_pressed_enter = False
        exit_requested = False
        while True:
            choice = process_input(
                f"{start}–{end} из {total}. Введите номер фильма для просмотра актеров, "
                f"f<номер> для добавления в избранное, Enter - продолжить, q - выход: ")
            # Позволяем прерывать просмотр страниц сразу из выбора номера
            if choice.lower() in ('q', 'quit', 'exit', 'esc'):
                exit_requested = True
                break
            if not choice:
                user_pressed_enter = True
                break
            
            # Обработка команды добавления в избранное
            if choice.lower().startswith('f'):
                try:
                    converted_choice = convert_layout_to_english(choice.lower())
                    film_num = int(converted_choice[1:])
                    if offset + 1 <= film_num <= offset + len(films):
                        film = films[film_num - offset - 1]
                        add_to_favorites(
                            film.get('film_id'),
                            film.get('title'),
                            film.get('release_year'),
                            film.get('rating')
                        )
                        print(f" ⭐ Фильм '{film.get('title')}' добавлен в избранное!")
                    else:
                        print(f" ⚠️  Неверный номер фильма (доступно: {offset + 1}-{offset + len(films)})")
                except (ValueError, IndexError):
                    print(" ⚠️  Неверный формат. Используйте: f<номер> (например, f5)")
                continue
            
            try:
                idx = int(choice)
                # индекс в returned `films` вычисляется относительно offset
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))

                    # Выбор актёра для просмотра его фильмов
                    if actors:
                        while True:
                            actor_choice = process_input(
                                "\n Выберите актёра для просмотра фильмов "
                                "(Enter — отмена): ")
                            if not actor_choice:
                                break
                            try:
                                actor_idx = int(actor_choice)
                                if 1 <= actor_idx <= len(actors):
                                    selected_actor = actors[actor_idx - 1]
                                    actor_id = selected_actor.get('actor_id')
                                    fn = selected_actor.get(
                                        'first_name', '').strip().title()
                                    ln = selected_actor.get(
                                        'last_name', '').strip().title()
                                    actor_name = f"{fn} {ln}"
                                    # Переход в просмотр фильмов актёра.
                                    # После возврата — показываем текущую страницу снова
                                    handle_actor_films(actor_id, actor_name)
                                    # Повторный вывод текущей страницы результатов
                                    print(f"\n{SEPARATOR_MINUS}\n")
                                    print_movies_table(
                                        films,
                                        offset=offset,
                                        total=total,
                                        show_header=False)
                                    print(SEPARATOR)
                                    break
                                else:
                                    print(
                                        f" Неверный номер — введите число от 1 до {
                                            len(actors)}")
                            except ValueError:
                                print(" Ожидался номер актёра.")
                else:
                    print(
                        f"Неверный номер — введите число от {
                            offset +
                            1} до {
                            offset +
                            len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        # Если это была последняя страница, не спрашиваем про следующую —
        # возвращаемся в меню
        if len(films) < LIMIT:
            break
        # Если пользователь запросил выход в выборе номера — прерываем сразу
        if exit_requested:
            break
        if user_pressed_enter:
            # Пользователь нажал Enter — перейти к следующей странице
            offset += LIMIT
            continue
        choice = process_input(
            "\n Нажмите Enter для продолжения или введите 'q' для выхода: ").lower()
        if choice in ('q', 'quit', 'exit', 'esc'):
            break
        offset += LIMIT


def handle_genre_search():
    """Поиск фильмов по жанру и диапазону лет (интерактивный режим).

    Пользователь выбирает жанр из списка и задаёт границы годов. Результаты
    показываются по страницам и логируются.
    """
    print("\n" + SEPARATOR_EQUAL)
    print(f"{' ПОИСК ПО ЖАНРУ И ГОДАМ':^60}")
    print(SEPARATOR_EQUAL + "\n")

    # Загрузка списка жанров из БД
    genres = get_genres()
    if not genres:
        print("  Список жанров пуст.\n")
        return
    print_genres(genres)
    try:
        idx = int(input(" Выберите номер жанра: ").strip())
        if not 1 <= idx <= len(genres):
            print("\n Неверный выбор\n")
            return
    except ValueError:
        print("\n Неверный ввод\n")
        return
    genre = genres[idx - 1]
    print(f"\n Выбран жанр: {genre.get('name')}\n")

    min_year, max_year = get_year_bounds()
    print(f" Доступные годы: {min_year} — {max_year}")
    lower = input(f" Нижний год (или Enter для {min_year}): ").strip()
    upper = input(f" Верхний год (или Enter для {max_year}): ").strip()
    try:
        y1 = int(lower) if lower else int(min_year)
        y2 = int(upper) if upper else int(max_year)
    except ValueError:
        print("\n Неверный формат года\n")
        return
    if y1 > y2:
        print("\n Нижний год больше верхнего\n")
        return
    print(f"\n Диапазон лет: {y1}–{y2}\n")

    # Опциональный рейтинг для жанра-поиска
    rating = None
    try:
        ratings = get_ratings()
        if ratings:
            print("Доступные рейтинги:")
            for i, r in enumerate(ratings, 1):
                desc = RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"{i}. {r} — {desc}")
            r_choice = input(
                "Выберите номер рейтинга (или Enter для пропуска): ").strip()
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
        total = get_genre_year_count(
            genre.get("category_id"), y1, y2, rating=rating)
        print(f"\n\n Найдено всего: {total} фильм(ов)\n")
    except Exception:
        total = None

    # Логируем сформированный запрос ОДИН раз (без offset)
    params = {
        "genre_id": genre.get("category_id"),
        "year_min": y1,
        "year_max": y2}
    if rating:
        params["rating"] = rating
    try:
        log_search("genre_year", params, int(
            total) if total is not None else 0)
    except Exception:
        pass

    offset = 0
    while True:
        films = search_by_genre_and_year(
            genre["category_id"],
            y1,
            y2,
            offset=offset,
            limit=LIMIT,
            rating=rating)
        # Если результатов нет на первой странице — возвращаемся в меню
        if not films and offset == 0:
            print("\n   Фильмы не найдены\n")
            break
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"{SEPARATOR_MINUS}\n")
            print_movies_table(
                films,
                offset=offset,
                total=total,
                show_header=False)
            print(SEPARATOR)
        else:
            print_movies_table(films, offset=offset, total=total)
            print(SEPARATOR)
        # После показа страницы — позволяем выбрать несколько фильмов подряд для просмотра актёров
        # Если пользователь сразу нажимает Enter (пустой ввод) — переходим дальше.
        # На последней странице выбор также доступен, но после него мы вернёмся в меню.
        user_pressed_enter = False
        exit_requested = False
        while True:
            choice = process_input(
                f"{start}–{end} из {total}. Введите номер фильма для просмотра актеров, "
                f"f<номер> для добавления в избранное, Enter - продолжить, q - выход: ")
            # Позволяем прерывать просмотр страниц сразу из выбора номера
            if choice.lower() in ('q', 'quit', 'exit', 'esc'):
                exit_requested = True
                break
            if not choice:
                user_pressed_enter = True
                break
            
            # Обработка команды добавления в избранное
            if choice.lower().startswith('f'):
                try:
                    converted_choice = convert_layout_to_english(choice.lower())
                    film_num = int(converted_choice[1:])
                    if offset + 1 <= film_num <= offset + len(films):
                        film = films[film_num - offset - 1]
                        add_to_favorites(
                            film.get('film_id'),
                            film.get('title'),
                            film.get('release_year'),
                            film.get('rating')
                        )
                        print(f" ⭐ Фильм '{film.get('title')}' добавлен в избранное!")
                    else:
                        print(f" ⚠️  Неверный номер фильма (доступно: {offset + 1}-{offset + len(films)})")
                except (ValueError, IndexError):
                    print(" ⚠️  Неверный формат. Используйте: f<номер> (например, f5)")
                continue
            
            try:
                idx = int(choice)
                if idx >= offset + 1 and idx <= offset + len(films):
                    film = films[idx - offset - 1]
                    actors = get_actors_by_film(film.get("film_id"))
                    print_actors(actors, film_title=film.get("title"))

                    # Выбор актёра для просмотра его фильмов
                    if actors:
                        while True:
                            actor_choice = process_input(
                                "\n Выберите актёра для просмотра фильмов "
                                "(Enter — отмена): ")
                            if not actor_choice:
                                break
                            try:
                                actor_idx = int(actor_choice)
                                if 1 <= actor_idx <= len(actors):
                                    selected_actor = actors[actor_idx - 1]
                                    actor_id = selected_actor.get('actor_id')
                                    fn = selected_actor.get(
                                        'first_name', '').strip().title()
                                    ln = selected_actor.get(
                                        'last_name', '').strip().title()
                                    actor_name = f"{fn} {ln}"
                                    # Переход в просмотр фильмов актёра.
                                    # После возврата — показываем текущую страницу снова
                                    handle_actor_films(actor_id, actor_name)
                                    # Повторный вывод текущей страницы результатов
                                    print(f"\n{SEPARATOR_MINUS}\n")
                                    print_movies_table(
                                        films,
                                        offset=offset,
                                        total=total,
                                        show_header=False)
                                    print(SEPARATOR)
                                    break
                                else:
                                    print(
                                        f" Неверный номер — введите число от 1 до {
                                            len(actors)}")
                            except ValueError:
                                print(" Ожидался номер актёра.")
                else:
                    print(
                        f"Неверный номер — введите число от {
                            offset +
                            1} до {
                            offset +
                            len(films)}")
            except ValueError:
                print("Ожидался номер фильма.")

        # Если это была последняя страница, не спрашиваем про следующую —
        # возвращаемся в меню
        if len(films) < LIMIT:
            break
        # Если пользователь запросил выход — прерываем сразу
        if exit_requested:
            break
        if user_pressed_enter:
            offset += LIMIT
            continue
        choice = process_input(
            "\n Нажмите Enter для продолжения или введите 'q' для выхода: ").lower()
        if choice in ('q', 'quit', 'exit', 'esc'):
            break
        offset += LIMIT
