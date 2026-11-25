"""Пример использования кольцевого двусвязного списка: плейлист.

Все переходы выполняет CircularDoublyLinkedList, а не Python list.
"""
from linked_list import CircularDoublyLinkedList


class Playlist:
    def __init__(self):
        self.songs = CircularDoublyLinkedList()

    def add_song(self, title):
        # По условию сайта новая песня всегда вставляется в начало.
        title = title.strip()
        if not title:
            raise ValueError("Введите название песни")
        self.songs.insert(0, title)
        # Новая песня становится первой и сразу выделяется курсором.
        self.songs.cursor = self.songs.head

    def next_song(self):
        # Изменяем только курсор. Начало списка (head) остаётся тем же.
        return self.songs.move_cursor(1)

    def previous_song(self):
        # Обратный переход по prev также не меняет порядок песен.
        return self.songs.move_cursor(-1)

    def remove_current(self):
        # Удаляем именно узел, на который указывает cursor.
        return self.songs.remove_cursor()

    def clear(self):
        self.songs.clear()

    def current_song(self):
        return self.songs.cursor.data if self.songs.cursor is not None else None

    def show(self):
        return {
            "titles": self.songs.iter(),
            "current": self.current_song(),
            "cursor_index": self.songs.cursor_index(),
            "count": self.songs.len(),
            "valid": self.songs.validate(),
        }


def create_playlist(titles=None, cursor_index=0):
    """Восстанавливаем объекты-узлы из сохранённых названий песен."""
    if titles is None:
        titles = ["Песня 1", "Песня 2", "Песня 3"]
    playlist = Playlist()
    # Используем низкоуровневый insert в конец для восстановления порядка.
    # Публичный метод add_song() всегда вставляет в начало.
    for title in titles:
        playlist.songs.insert(playlist.songs.len(), title)
    if playlist.songs.len():
        if not isinstance(cursor_index, int) or not 0 <= cursor_index < playlist.songs.len():
            cursor_index = 0
        playlist.songs.cursor = playlist.songs.node_at(cursor_index)
    return playlist
