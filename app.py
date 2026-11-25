"""Учебный сайт: связные списки на Python + Flask, без JavaScript.

Каждая кнопка отправляет HTML-форму. Flask меняет список и заново
отображает страницу. Состояние текущего пользователя хранится в session.
"""

import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from linked_list import SinglyLinkedList, DoublyLinkedList, CircularDoublyLinkedList
from playlist import create_playlist
import secrets
app = Flask(__name__)
# Для учебного локального запуска; при публикации задайте SECRET_KEY в окружении.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-key-for-public-use")

TYPES = {
    "singly": ("Односвязный", SinglyLinkedList),
    "doubly": ("Двусвязный", DoublyLinkedList),
    "circular": ("Кольцевой двусвязный", CircularDoublyLinkedList),
}
MAX_ELEMENTS = 30  # небольшое ограничение для наглядной схемы и cookie


def load_list():
    """Восстанавливает нашу структуру из данных сессии."""
    kind = session.get("kind", "circular")
    if kind not in TYPES:
        kind = "circular"

    list_class = TYPES[kind][1]
    linked_list = list_class()
    values = session.get("values", [10, 20, 30])

    for value in values:
        linked_list.insert(linked_list.len(), value)

    # Восстанавливаем курсор на нужном узле.
    cursor_index = session.get("cursor", 0)
    if values and isinstance(cursor_index, int) and 0 <= cursor_index < len(values):
        linked_list.cursor = linked_list.node_at(cursor_index)
    elif values:
        linked_list.cursor = linked_list.head

    return kind, linked_list


def save_list(kind, linked_list):
    """Сохраняет значения и позицию курсора после операции."""
    session["kind"] = kind
    session["values"] = linked_list.iter()
    session["cursor"] = linked_list.cursor_index()


def read_number(field_name):
    """Получает целое число из формы и объясняет ошибку ввода."""
    raw_value = request.form.get(field_name, "").strip()
    try:
        return int(raw_value)
    except ValueError:
        raise ValueError(f"Поле «{field_name}»: введите целое число")

RUN_ID = secrets.token_hex(16)

@app.before_request
def reset_previous_run():
    if session.get("run_id") != RUN_ID:
        session.clear()
        session["run_id"] = RUN_ID

@app.route("/", methods=["GET", "POST"])
def home():
    kind, linked_list = load_list()

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            # Пока выполняется пошаговый сдвиг, остальные операции не разрешены.
            pending = session.get("shift_steps")
            if pending is not None and action not in ("shift_next", "shift_cancel"):
                raise ValueError("Сначала завершите или отмените пошаговый сдвиг")

            if action == "choose_type":
                new_kind = request.form.get("kind", "")
                if new_kind not in TYPES:
                    raise ValueError("Неизвестный вид списка")
                # Переносим значения в другой вид списка.
                values = linked_list.iter()
                new_list = TYPES[new_kind][1]()
                for value in values:
                    new_list.insert(new_list.len(), value)
                old_cursor = linked_list.cursor_index()
                if old_cursor is not None and new_list.len():
                    new_list.cursor = new_list.node_at(old_cursor)
                kind, linked_list = new_kind, new_list
                flash("Вид списка изменён", "success")

            elif action in ("add_front", "add_back", "add_at", "add_after_cursor"):
                if linked_list.len() >= MAX_ELEMENTS:
                    raise ValueError("Для наглядности разрешено не более 30 элементов")
                value = read_number("value")
                if action == "add_front":
                    linked_list.insert(0, value)
                elif action == "add_back":
                    linked_list.insert(linked_list.len(), value)
                elif action == "add_at":
                    linked_list.insert(read_number("index"), value)
                else:
                    linked_list.insert_after_cursor(value)
                flash(f"Добавлен элемент {value}", "success")

            elif action in ("remove_front", "remove_back", "remove_at", "remove_cursor"):
                if not linked_list.len():
                    raise ValueError("Список пуст")
                if action == "remove_front":
                    removed = linked_list.remove_at(0)
                elif action == "remove_back":
                    removed = linked_list.remove_at(linked_list.len() - 1)
                elif action == "remove_at":
                    removed = linked_list.remove_at(read_number("index"))
                else:
                    removed = linked_list.remove_cursor()
                flash(f"Удалён элемент {removed}", "success")

            elif action == "next":
                linked_list.move_cursor(1)
                flash("Курсор перемещён вперёд", "success")

            elif action == "previous":
                linked_list.move_cursor(-1)
                flash("Курсор перемещён назад", "success")

            elif action in ("rotate", "shift_start"):
                steps = read_number("steps")
                direction = request.form.get("direction", "left")
                if steps < 0:
                    raise ValueError("Число шагов должно быть неотрицательным")
                if direction not in ("left", "right"):
                    raise ValueError("Выберите направление сдвига")
                if not linked_list.circular:
                    raise ValueError("Сдвиг доступен только для кольцевого списка")
                if not linked_list.len():
                    raise ValueError("Список пуст")
                # Полные обороты тоже показываем в пошаговом режиме,
                # чтобы было видно все запрошенные пользователем шаги.
                if action == "rotate":
                    linked_list.rotate(steps, direction)
                    flash(f"Выполнен сдвиг на {steps} шаг(ов): "
                          f"{'влево' if direction == 'left' else 'вправо'}", "success")
                else:
                    if steps == 0:
                        flash("Сдвиг на 0 шагов: список не изменился", "success")
                    else:
                        session["shift_steps"] = steps
                        session["shift_total"] = steps
                        session["shift_direction"] = direction
                        flash("Пошаговый сдвиг подготовлен. Нажмите «Следующий шаг»", "success")

            elif action == "shift_next":
                if session.get("shift_steps") is None:
                    raise ValueError("Пошаговый сдвиг не запущен")
                direction = session["shift_direction"]
                linked_list.rotate(1, direction)
                remaining = session["shift_steps"] - 1
                done = session["shift_total"] - remaining
                if remaining == 0:
                    session.pop("shift_steps", None)
                    session.pop("shift_total", None)
                    session.pop("shift_direction", None)
                    flash(f"Шаг {done} выполнен. Пошаговый сдвиг завершён", "success")
                else:
                    session["shift_steps"] = remaining
                    flash(f"Выполнен шаг {done}. Осталось: {remaining}", "success")

            elif action == "shift_cancel":
                session.pop("shift_steps", None)
                session.pop("shift_total", None)
                session.pop("shift_direction", None)
                flash("Пошаговый режим завершён (выполненные шаги сохранены)", "success")

            elif action == "clear":
                linked_list.clear()
                flash("Список очищен", "success")

            elif action == "example":
                linked_list.clear()
                for value in (10, 20, 30):
                    linked_list.insert(linked_list.len(), value)
                flash("Загружен пример: 10, 20, 30", "success")
            else:
                raise ValueError("Неизвестная команда")

            if not linked_list.validate():
                raise RuntimeError("Нарушена целостность списка")
            save_list(kind, linked_list)

        except (IndexError, ValueError) as error:
            flash(str(error), "error")

        # После нажатия курсора возвращаемся к той же области страницы.
        # Фрагмент #cursor-controls не передаётся серверу и работает без JavaScript.
        if action in ("next", "previous"):
            return redirect(url_for("home") + "#cursor-controls")
        return redirect(url_for("home"))

    values = linked_list.iter()
    cursor_index = linked_list.cursor_index()
    return render_template(
        "index.html",
        kind=kind,
        kinds=TYPES,
        values=values,
        cursor_index=cursor_index,
        valid=linked_list.validate(),
        circular=linked_list.circular,
        doubly=linked_list.doubly,
        shift_remaining=session.get("shift_steps"),
        shift_total=session.get("shift_total"),
        shift_direction=session.get("shift_direction"),
    )


@app.route("/playlist", methods=["GET", "POST"])
def playlist_page():
    """Страница плейлиста с фиксированным кольцевым двусвязным списком."""
    default_titles = ["Песня 1", "Песня 2", "Песня 3"]
    titles = session.get("playlist_titles", default_titles)
    cursor_index = session.get("playlist_cursor", 0)
    playlist = create_playlist(titles, cursor_index)

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "playlist_add":
                if playlist.songs.len() >= MAX_ELEMENTS:
                    raise ValueError("Разрешено не более 30 песен")
                title = request.form.get("title", "").strip()
                if len(title) > 80:
                    raise ValueError("Название не должно быть длиннее 80 символов")
                playlist.add_song(title)
                flash(f"Песня «{title}» добавлена в начало", "success")

            elif action == "playlist_remove":
                if playlist.songs.len() == 0:
                    raise ValueError("Плейлист пуст. Удалять нечего")
                removed = playlist.remove_current()
                flash(f"Удалена песня «{removed}»", "success")

            elif action == "playlist_next":
                playlist.next_song()
                flash("Выбрана следующая песня", "success")

            elif action == "playlist_previous":
                playlist.previous_song()
                flash("Выбрана предыдущая песня", "success")

            elif action == "playlist_clear":
                playlist.clear()
                flash("Плейлист очищен", "success")

            elif action == "playlist_reset":
                playlist = create_playlist(default_titles, 0)
                flash("Загружен пример из трёх песен", "success")

            else:
                raise ValueError("Неизвестная команда плейлиста")

            if not playlist.songs.validate():
                raise RuntimeError("Нарушены кольцевые связи плейлиста")

            # Порядок песен сохраняем только при изменении состава плейлиста.
            # Кнопки «Предыдущая» и «Следующая» изменяют только курсор:
            # это не сдвиг HEAD и не перестановка композиций.
            if action not in ("playlist_next", "playlist_previous"):
                session["playlist_titles"] = playlist.songs.iter()
            session["playlist_cursor"] = playlist.songs.cursor_index()

        except (ValueError, IndexError) as error:
            flash(str(error), "error")

        return redirect(url_for("playlist_page") + "#playlist-view")

    return render_template("playlist.html", playlist=playlist.show())


if __name__ == "__main__":
    app.run(debug=True)
