"""Консольное интерактивное приложение для поиска фильмов.
Модуль содержит текстовое меню приложения для работы с базой Sakila.
Функции поиска вынесены в модуль `searches`.
Основная функция:
- `main` — цикл главного меню приложения.
"""

from log_stats import get_top_queries, get_last_queries, clear_logs
from formatter import print_stats, SEPARATOR, SEPARATOR_EQUAL
from searches import handle_keyword_search, handle_genre_search
from favorites import view_favorites, clear_favorites
from input_utils import process_yes_no_input


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

        choice = input("\n Выберите опцию: ").strip()

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
            if process_yes_no_input(
                    "\n  Это удалит ВСЕ сохранённые запросы в MongoDB. Продолжить? (y/n): "):
                try:
                    deleted = clear_logs()
                    print(f"\n Удалено документов: {deleted}")
                    print(SEPARATOR)
                except Exception as exc:
                    print(f"\n Не удалось очистить логи: {exc}")
            else:
                print("\n Операция отменена.")
                print(SEPARATOR)

        elif choice == "5":
            view_favorites()
            print(SEPARATOR)

        elif choice == "6":
            clear_favorites()
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
