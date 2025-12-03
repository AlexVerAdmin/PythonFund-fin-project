"""Модуль для управления избранными фильмами.
Хранит избранные фильмы в локальном JSON файле.
Содержит функции для работы с данными и обработчики для меню.
"""

import json
import os
from datetime import datetime


FAVORITES_FILE = 'favorites.json'


def load_favorites():
    """Загружает избранные фильмы из JSON файла.
    Возвращает:
        dict: Словарь с ключом 'films' содержащий список избранных фильмов
    """
    if not os.path.exists(FAVORITES_FILE):
        return {"films": []}

    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError): # перехватываетсразу двеошибки,
        # если файл повреждён или недоступен
        return {"films": []}


def add_to_favorites(film_id, title, year=None, age_rating=None):
    """Добавляет фильм в избранное.
    Параметры:
        film_id: ID фильма в базе данных
        title: Название фильма
        year: Год выпуска (опционально)
        age_rating: Возрастной рейтинг (опционально)
    Возвращает:
        bool: True если фильм добавлен, False если уже в избранном
    """
    # Проверяем, нет ли уже такого фильма
    if is_favorite(film_id):
        return False
    
    data = load_favorites()

    film_data = {
        'film_id': film_id,
        'title': title,
        'added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if year:
        film_data['year'] = year
    if age_rating:
        film_data['age_rating'] = age_rating

    data['films'].append(film_data)
    
    # Сохраняем в файл
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка сохранения избранного: {e}")
        return False
    
    return True


def is_favorite(film_id):
    """Проверяет, находится ли фильм в избранном.
    Параметры:
        film_id: ID фильма для проверки
    Возвращает:
        bool: True если фильм в избранном
    """
    data = load_favorites()
    return any(f['film_id'] == film_id for f in data['films'])


def clear_favorites():
    """Очищает весь список избранногопосле подтверждения.
    Возвращает:
        int: Количество удалённых фильмов
    """
    from input_utils import process_yes_no_input
    
    data = load_favorites()
    count = len(data['films'])

    if count == 0:
        print("\n  Список избранного уже пуст.\n")
        return

    if not process_yes_no_input(  # input_utils.py
            f"\n  Это удалит ВСЕ {count} фильм(ов) из избранного. Продолжить? (y/n): "):
        print("\n  Операция отменена.\n")
        return
    
    data['films'] = []
    
    # Сохраняем в файл
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  Удалено фильмов из избранного: {count}\n")
    except IOError as e:
        print(f"Ошибка сохранения избранного: {e}")


def view_favorites():
    """Показывает все избранные фильмы с возможностью просмотра актёров."""
    from formatter import print_movies_table, print_actors, SEPARATOR, SEPARATOR_EQUAL, SEPARATOR_MINUS
    from mysql_connector import get_actors_by_film
    from input_utils import process_input
    
    print("\n" + SEPARATOR_EQUAL)
    print(f"{' МОИ ИЗБРАННЫЕ ФИЛЬМЫ':^70}")
    print(SEPARATOR_EQUAL + "\n")

    data = load_favorites() 
    favorites = data['films'] 

    if not favorites:
        print("  Список избранного пуст.\n")
        print("  Добавляйте фильмы в избранное во время поиска (нажмите 'f').\n")
        return

    print(f" Всего в избранном: {len(favorites)} фильм(ов)\n")

    # Преобразуем в формат для print_movies_table
    films_for_display = []
    for fav in favorites:
        film = {
            'film_id': fav['film_id'],
            'title': fav['title'],
            'release_year': fav.get('year', 'N/A'),
            'rating': fav.get('rating', 'N/A'),
            'rental_rate': None,
            'replacement_cost': None,
            'description': f"Добавлено: {fav['added']}"
        }
        films_for_display.append(film)

    print_movies_table(films_for_display, show_header=False)  # formatter.py
    print(SEPARATOR)
    
    # Интерактивное взаимодействие
    while True:
        choice = process_input(  # input_utils.py
            "\n Введите номер фильма для просмотра актёров или 'q' для выхода: "
        )
        
        if choice.lower() == 'q' or not choice:
            break
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(films_for_display):
                film = films_for_display[idx - 1]
                actors = get_actors_by_film(film.get("film_id"))  # mysql_connector.py
                print_actors(actors, film_title=film.get("title"))  # formatter.py

                # Выбор актёра для просмотра его фильмов
                if actors:
                    while True:
                        actor_choice = process_input(  # input_utils.py
                            "\n Выберите актёра для просмотра фильмов "
                            "(Enter — отмена): ")
                        if not actor_choice:
                            break
                        try:
                            actor_idx = int(actor_choice)
                            if 1 <= actor_idx <= len(actors):
                                from searches import show_actor_films
                                selected_actor = actors[actor_idx - 1]
                                actor_id = selected_actor.get('actor_id')
                                fn = selected_actor.get('first_name', '').strip().title()
                                ln = selected_actor.get('last_name', '').strip().title()
                                actor_name = f"{fn} {ln}"
                                show_actor_films(actor_id, actor_name)  # searches.py
                                
                                # Повторный вывод списка избранного
                                print("\n" + SEPARATOR_EQUAL)
                                print(f"{' МОИ ИЗБРАННЫЕ ФИЛЬМЫ':^70}")
                                print(SEPARATOR_EQUAL + "\n")
                                print(f" Всего в избранном: {len(favorites)} фильм(ов)\n")
                                print_movies_table(films_for_display, show_header=False)  # formatter.py
                                print(SEPARATOR)
                                break
                            else:
                                print(f" Неверный номер — введите число от 1 до {len(actors)}")
                        except ValueError:
                            print(" Ожидался номер актёра.")
            else:
                print(f"Неверный номер — введите число от 1 до {len(films_for_display)}")
        except ValueError:
            print("Ожидался номер фильма.")

