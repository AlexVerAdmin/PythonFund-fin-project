"""Консольное интерактивное приложение для поиска фильмов.
Модуль содержит текстовое меню приложения для работы с базой Sakila.
Функции поиска вынесены в модуль `searches`.
Основная функция:
- `main` — цикл главного меню приложения.
"""

from log_stats import get_top_queries, get_last_queries, clear_logs
from formatter import print_stats, SEPARATOR, SEPARATOR_EQUAL
from searches import search_by_keyword_interactive, search_by_genre_interactive
from favorites import view_favorites, clear_favorites
from input_utils import process_yes_no_input, process_input


def main():
    """Главное меню приложения с интерактивным управлением."""

    print(f"\n{'ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ ПОИСКА ФИЛЬМОВ':^60}")
    print(f"{'База данных: Sakila':^60}\n")

    while True:
        print(SEPARATOR_EQUAL)
        print(f"{' ГЛАВНОЕ МЕНЮ':^60}")
        print(SEPARATOR_EQUAL)
        print("  1.  Поиск по ключевому слову")
        print("  2.  Поиск по жанру и/или диапазону лет")
        print("  3.  Показать статистику запросов")
        print("  4.  Очистить логи MongoDB")
        print("  5.  Просмотр избранного")
        print("  6.  Очистить избранное")
        print("  q.  Выход")
        print(SEPARATOR_EQUAL)

        choice = process_input("\n Выберите опцию: ")  # input_utils.py

        if choice == "1":
            search_by_keyword_interactive()  # searches.py

        elif choice == "2":
            search_by_genre_interactive()  # searches.py

        elif choice == "3":
            top_q = get_top_queries()  # log_stats.py
            last_q = get_last_queries()  # log_stats.py
            print_stats(top_q, last_q)  # formatter.py
            print(SEPARATOR)

        elif choice == "4":
            prompt = (
                "\n  Это удалит ВСЕ сохранённые запросы в MongoDB. "
                "Продолжить? (y/n): "
            )
            if process_yes_no_input(prompt):  # input_utils.py
                try:
                    deleted = clear_logs()  # log_stats.py
                    print(f"\n Удалено документов: {deleted}")
                    print(SEPARATOR)
                except Exception as exc:
                    print(f"\n Не удалось очистить логи: {exc}")
            else:
                print("\n Операция отменена.")
                print(SEPARATOR)

        elif choice == "5":
            view_favorites()  # favorites.py
            print(SEPARATOR)

        elif choice == "6":
            clear_favorites()  # favorites.py
            print(SEPARATOR)

        elif choice.lower() == 'q':
            print("\n" + SEPARATOR_EQUAL)
            print(f"{' До встречи!':^60}")
            print(SEPARATOR_EQUAL + "\n")
            break

        else:
            print("\n Неверная опция. Пожалуйста, выберите 1-6 или q.\n")


if __name__ == "__main__":
    main()
