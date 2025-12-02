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
    get_age_ratings,
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
from config import LIMIT, AGE_RATING_DESCRIPTIONS
from input_utils import process_yes_no_input, process_input, convert_layout_to_english
from favorites import add_to_favorites


def _get_year_input(prompt, min_year, max_year, allow_empty=True):
    """Запрашивает ввод года с валидацией.
    
    Параметры:
        prompt: Текст приглашения для ввода
        min_year: Минимально допустимый год
        max_year: Максимально допустимый год
        allow_empty: Разрешить пустой ввод (Enter)
    
    Возвращает:
        int или None: Введённый год или None если пользователь нажал Enter
    """
    while True:
        year_input = input(prompt).strip()
        if not year_input:
            if allow_empty:
                return None
            continue
        try:
            year = int(year_input)
            if year < 0 or len(year_input) != 4:
                print("Год должен быть четырёхзначным положительным числом. Попробуйте снова.")
                continue
            if year < int(min_year) or year > int(max_year):
                print(f"Год должен быть в диапазоне {min_year}—{max_year}. Попробуйте снова.")
                continue
            return year
        except ValueError:
            print("Неверный формат. Введите четырёхзначное число.")


def _handle_add_to_favorites(choice, films, offset=0):
    """Обрабатывает команду добавления фильма в избранное.
    
    Параметры:
        choice: Строка ввода пользователя (например, 'f5' или 'а5')
        films: Список фильмов на текущей странице
        offset: Смещение для нумерации (0 для handle_actor_films, >0 для поисковых функций)
    
    Возвращает:
        bool: True если команда успешно обработана, False в случае ошибки
    """
    try:
        converted_choice = convert_layout_to_english(choice)
        film_num = int(converted_choice[1:])
        
        # Проверка диапазона в зависимости от offset
        if offset == 0:
            # Для handle_actor_films: нумерация от 1 до len(films)
            if 1 <= film_num <= len(films):
                film = films[film_num - 1]
            else:
                print(f" ⚠️  Неверный номер фильма (доступно: 1-{len(films)})")
                return False
        else:
            # Для поисковых функций: нумерация с учётом offset
            if offset + 1 <= film_num <= offset + len(films):
                film = films[film_num - offset - 1]
            else:
                print(f" ⚠️  Неверный номер фильма (доступно: {offset + 1}-{offset + len(films)})")
                return False
        
        add_to_favorites(
            film.get('film_id'),
            film.get('title'),
            film.get('release_year'),
            film.get('age_rating')
        )
        print(f" ⭐ Фильм '{film.get('title')}' добавлен в избранное!")
        return True
    except (ValueError, IndexError):
        print(" ⚠️  Неверный формат. Используйте: f<номер> (например, f3)")
        return False


def _paginate_search_results(search_func, total, **search_params):
    """Универсальная функция пагинации результатов поиска.
    
    Параметры:
        search_func: Функция поиска (search_by_keyword или search_by_genre_and_year)
        total: Общее количество результатов
        **search_params: Параметры для передачи в search_func (keyword, genre_id, year_min, year_max, age_rating)
    """
    offset = 0
    while True:
        films = search_func(offset=offset, limit=LIMIT, **search_params)
        
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
        
        # После показа страницы — позволяем выбрать один или несколько фильмов подряд
        # Если пользователь сразу нажимает Enter (пустой ввод) — переходим дальше.
        # На последней странице выбор также доступен, но после него мы вернёмся в меню.
        user_pressed_enter = False
        exit_requested = False
        while True:
            choice = process_input(
                f"{start}–{end} из {total}. Введите номер фильма для просмотра актеров, "
                f"f<номер> для добавления в избранное, Enter - продолжить, q - выход: ")
            
            # Позволяем прерывать просмотр страниц сразу из выбора номера
            if choice.lower() == 'q':
                exit_requested = True
                break
            if not choice:
                user_pressed_enter = True
                break
            
            # Обработка команды добавления в избранное
            if choice.lower().startswith('f'):
                _handle_add_to_favorites(choice.lower(), films, offset)
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
                                    fn = selected_actor.get('first_name', '').strip().title()
                                    ln = selected_actor.get('last_name', '').strip().title()
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
                                    print(f" Неверный номер — введите число от 1 до {len(actors)}")
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
        if choice == 'q':
            break
        offset += LIMIT


def handle_actor_films(actor_id, actor_name):
    """Показать все фильмы с участием выбранного актёра.

    Args:
        actor_id: ID актёра в базе данных
        actor_name: Полное имя актёра для отображения
    """
    print("\n" + SEPARATOR_EQUAL)
    print(f"{f' ФИЛЬМЫ С УЧАСТИЕМ: {actor_name}':^70}")
    print(SEPARATOR_EQUAL + "\n")

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
        if choice == 'q':
            break
        
        # Обработка команды добавления в избранное
        if choice.startswith('f'):
            _handle_add_to_favorites(choice, films, offset=offset)
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
        " Введите ключевое слово (Enter для поиска всех фильмов, q для отмены): ")
    if keyword.lower() == 'q':
        print("\n Отмена поиска, возвращаюсь в меню.\n")
        return
    
    # Пустой ввод означает поиск по всем фильмам (keyword = None или пустая строка)
    if not keyword:
        keyword = None
        print("\n Поиск по всем фильмам.\n")

    # Опциональный жанр
    genre_id = None
    if process_yes_no_input("\n Фильтровать по жанру? (y/n): "):
        genres = get_genres()
        if not genres:
            print("\n  Список жанров пуст, фильтр по жанру пропущен.\n")
        else:
            print_genres(genres)
            while True:
                try:
                    idx_input = input(" Выберите номер жанра (или Enter для отмены): ").strip()
                    if not idx_input:
                        break
                    idx = int(idx_input)
                    if 1 <= idx <= len(genres):
                        genre_id = genres[idx - 1].get("category_id")
                        print(f"\n Выбран жанр: {genres[idx - 1].get('name')}\n")
                        break
                    else:
                        print(f"Неверный номер. Введите число от 1 до {len(genres)}")
                except ValueError:
                    print("Неверный формат. Введите номер жанра.")

    # Опциональные года
    year_min = year_max = None
    try:
        min_year, max_year = get_year_bounds()
        print(f"\n Доступные годы: {min_year} — {max_year}")
        
        # Ввод нижнего года с валидацией (по умолчанию min_year)
        year_input = _get_year_input(f" Нижний год (Enter для {min_year}): ", min_year, max_year, allow_empty=True)
        y1 = year_input if year_input is not None else int(min_year)
        
        # Ввод верхнего года с валидацией (по умолчанию max_year)
        year_input = _get_year_input(f" Верхний год (Enter для {max_year}): ", min_year, max_year, allow_empty=True)
        y2 = year_input if year_input is not None else int(max_year)
        
        if y1 <= y2:
            year_min, year_max = y1, y2
            print(f"\n Диапазон лет: {y1}–{y2}\n")
        else:
            print("\n Неправильный диапазон лет, фильтр по годам пропущен.\n")
    except Exception:
        # Если не удалось получить границы — пропускаем
        year_min = year_max = None

    # Опциональная возрастная категория
    age_rating = None
    try:
        ratings = get_age_ratings()
        if ratings:
            print("Доступные возрастные категории:")
            for i, r in enumerate(ratings, 1):
                desc = AGE_RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"{i}. {r} — {desc}")
            r_choice = input(
                "\n Выберите номер категории (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    age_rating = ratings[ri - 1]
                else:
                    print("Неверный выбор категории, пропускаю фильтр.")
    except Exception:
        age_rating = None

    # Подсчёт общего числа совпадений по сформированному запросу
    try:
        total = get_keyword_count(
            keyword,
            genre_id=genre_id,
            year_min=year_min,
            year_max=year_max,
            age_rating=age_rating)
        print(f"\n\n Найдено всего: {total} фильм(ов)\n")
    except Exception:
        total = None

    # Логируем сам запрос ОДИН раз (без offset)
    params = {"keyword": keyword}
    if genre_id is not None:
        params["genre_id"] = genre_id
    if year_min is not None and year_max is not None:
        params.update({"year_min": year_min, "year_max": year_max})
    if age_rating:
        params["age_rating"] = age_rating
    
    log_search("keyword", params, int(total) if total is not None else 0)

    # Постраничный вывод результатов
    _paginate_search_results(
        search_by_keyword,
        total,
        keyword=keyword,
        genre_id=genre_id,
        year_min=year_min,
        year_max=year_max,
        age_rating=age_rating
    )


def handle_genre_search():
    """Поиск фильмов по жанру и/или диапазону лет (интерактивный режим).

    Пользователь может выбрать жанр, диапазон лет или оба параметра. Результаты
    показываются по страницам и логируются.
    """
    print("\n" + SEPARATOR_EQUAL)
    print(f"{' ПОИСК ПО ЖАНРУ И/ИЛИ ГОДАМ':^60}")
    print(SEPARATOR_EQUAL + "\n")

    # Опциональный жанр
    genre_id = None
    genre_name = None
    genres = get_genres()
    if not genres:
        print("  Список жанров пуст.\n")
    else:
        print_genres(genres)
        while True:
            try:
                idx_input = input(" Выберите номер жанра (или Enter для пропуска): ").strip()
                if not idx_input:
                    break
                idx = int(idx_input)
                if 1 <= idx <= len(genres):
                    genre_id = genres[idx - 1].get("category_id")
                    genre_name = genres[idx - 1].get('name')
                    print(f"\n Выбран жанр: {genre_name}\n")
                    break
                else:
                    print(f" ⚠️  Неверный номер. Введите число от 1 до {len(genres)}")
            except ValueError:
                print(" ⚠️  Неверный формат. Введите номер жанра.")

    # Опциональные года
    y1 = y2 = None
    try:
        min_year, max_year = get_year_bounds()
        print(f" Доступные годы: {min_year} — {max_year}")
        
        # Ввод нижнего года с валидацией (можно пропустить)
        y1 = _get_year_input(f" Нижний год (Enter для пропуска): ", min_year, max_year, allow_empty=True)
        
        # Ввод верхнего года с валидацией (можно пропустить)
        y2 = _get_year_input(f" Верхний год (Enter для пропуска): ", min_year, max_year, allow_empty=True)
        
        # Если ввели только один год, используем границы по умолчанию для второго
        if y1 is not None and y2 is None:
            y2 = int(max_year)
        elif y2 is not None and y1 is None:
            y1 = int(min_year)
        
        if y1 is not None and y2 is not None:
            if y1 > y2:
                print("\nНижний год больше верхнего, фильтр по годам пропущен.\n")
                y1 = y2 = None
            else:
                print(f"\n Диапазон лет: {y1}–{y2}\n")
    except Exception:
        print("\n Ошибка получения границ лет, фильтр по годам пропущен.\n")
        y1 = y2 = None
    
    # Проверка, что хотя бы один параметр задан
    if genre_id is None and (y1 is None or y2 is None):
        print("\n Не заданы параметры поиска. Возвращаюсь в меню.\n")
        return

    # Опциональная возрастная категория
    age_rating = None
    try:
        ratings = get_age_ratings()
        if ratings:
            print("Доступные возрастные категории:")
            for i, r in enumerate(ratings, 1):
                desc = AGE_RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"{i}. {r} — {desc}")
            r_choice = input(
                "\n Выберите номер категории (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    age_rating = ratings[ri - 1]
                else:
                    print("Неверный выбор категории, пропускаю фильтр.")
    except Exception:
        age_rating = None

    # Показать общее количество совпадений перед пагинацией
    y1 = y2 = None
    try:
        min_year, max_year = get_year_bounds()
        print(f" Доступные годы: {min_year} — {max_year}")
        
        # Ввод нижнего года с валидацией (можно пропустить)
        y1 = _get_year_input(f" Нижний год (Enter для пропуска): ", min_year, max_year, allow_empty=True)
        
        # Ввод верхнего года с валидацией (можно пропустить)
        y2 = _get_year_input(f" Верхний год (Enter для пропуска): ", min_year, max_year, allow_empty=True)
        
        # Если ввели только один год, используем границы по умолчанию для второго
        if y1 is not None and y2 is None:
            y2 = int(max_year)
        elif y2 is not None and y1 is None:
            y1 = int(min_year)
        
        if y1 is not None and y2 is not None:
            if y1 > y2:
                print("\nНижний год больше верхнего, фильтр по годам пропущен.\n")
                y1 = y2 = None
            else:
                print(f"\n Диапазон лет: {y1}–{y2}\n")
    except Exception:
        print("\n Ошибка получения границ лет, фильтр по годам пропущен.\n")
        y1 = y2 = None
    
    # Проверка, что хотя бы один параметр задан
    if genre_id is None and (y1 is None or y2 is None):
        print("\n Не заданы параметры поиска. Возвращаюсь в меню.\n")
        return

    # Опциональная возрастная категория  
    age_rating = None
    try:
        ratings = get_age_ratings()
        if ratings:
            print("Доступные возрастные категории:")
            for i, r in enumerate(ratings, 1):
                desc = AGE_RATING_DESCRIPTIONS.get(r, "(описание отсутствует)")
                print(f"{i}. {r} — {desc}")
            r_choice = input(
                "\n Выберите номер категории (или Enter для пропуска): ").strip()
            if r_choice:
                ri = int(r_choice)
                if 1 <= ri <= len(ratings):
                    age_rating = ratings[ri - 1]
                else:
                    print("Неверный выбор категории, пропускаю фильтр.")
    except Exception:
        age_rating = None

    # Показать общее количество совпадений перед пагинацией
    try:
        total = get_genre_year_count(
            genre_id=genre_id, year_min=y1, year_max=y2, age_rating=age_rating)
        print(f"\n\n Найдено всего: {total} фильм(ов)\n")
    except Exception:
        total = None

    # Логируем сформированный запрос ОДИН раз (без offset)
    params = {}
    if genre_id is not None:
        params["genre_id"] = genre_id
    if y1 is not None and y2 is not None:
        params.update({"year_min": y1, "year_max": y2})
    if age_rating:
        params["age_rating"] = age_rating
    
    log_search("genre_year", params, int(total) if total is not None else 0)

    # Постраничный вывод результатов
    _paginate_search_results(
        search_by_genre_and_year,
        total,
        genre_id=genre_id,
        year_min=y1,
        year_max=y2,
        age_rating=age_rating
    )
