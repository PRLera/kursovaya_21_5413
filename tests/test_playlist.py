"""Проверка логики плейлиста без браузера."""
import unittest
from playlist import Playlist, create_playlist


class PlaylistTests(unittest.TestCase):
    def test_example(self):
        p = create_playlist()
        self.assertEqual(p.show()['titles'], ['Песня 1', 'Песня 2', 'Песня 3'])
        self.assertTrue(p.songs.validate())

    def test_insert_always_at_front(self):
        p = create_playlist()
        p.add_song('Новая песня')
        self.assertEqual(p.show()['titles'][0], 'Новая песня')
        self.assertEqual(p.current_song(), 'Новая песня')
        self.assertTrue(p.songs.validate())

    def test_add_multiple_songs_at_beginning(self):
        p = create_playlist()
        p.add_song('Новая 1')
        p.add_song('Новая 2')
        self.assertEqual(p.songs.iter(), ['Новая 2', 'Новая 1', 'Песня 1', 'Песня 2', 'Песня 3'])
        self.assertEqual(p.songs.cursor_index(), 0)
        self.assertTrue(p.songs.validate())

    def test_remove_cursor(self):
        p = create_playlist()
        p.next_song()
        self.assertEqual(p.remove_current(), 'Песня 2')
        self.assertEqual(p.show()['titles'], ['Песня 1', 'Песня 3'])
        self.assertTrue(p.songs.validate())

    def test_wraps_both_ways(self):
        p = create_playlist()
        self.assertEqual(p.previous_song(), 'Песня 3')
        self.assertEqual(p.next_song(), 'Песня 1')

    def test_clear_and_add_again(self):
        p = create_playlist()
        p.clear()
        self.assertIsNone(p.current_song())
        self.assertTrue(p.songs.validate())
        p.add_song('Одна песня')
        self.assertEqual(p.next_song(), 'Одна песня')
        self.assertTrue(p.songs.validate())

    def test_cursor_navigation_does_not_reorder(self):
        p = create_playlist(['Первая', 'Вторая', 'Третья', 'Четвёртая'], 0)
        expected = p.songs.iter()
        head = p.songs.head
        tail = p.songs.tail
        for _ in range(13):
            p.next_song()
            self.assertEqual(p.songs.iter(), expected)
            self.assertIs(p.songs.head, head)
            self.assertIs(p.songs.tail, tail)
            self.assertTrue(p.songs.validate())
        for _ in range(11):
            p.previous_song()
            self.assertEqual(p.songs.iter(), expected)
            self.assertIs(p.songs.head, head)
            self.assertIs(p.songs.tail, tail)
            self.assertTrue(p.songs.validate())

    def test_restore_after_each_cursor_move(self):
        # Имитируем сохранение и восстановление между запросами Flask.
        titles = ['А', 'Б', 'В']
        index = 0
        for direction in [1, 1, 1, -1, 1, -1, -1]:
            p = create_playlist(titles, index)
            p.songs.move_cursor(direction)
            index = p.songs.cursor_index()
            self.assertEqual(p.songs.iter(), titles)
            self.assertTrue(p.songs.validate())
        self.assertEqual(index, 1)

    def test_add_then_navigation_keeps_order(self):
        p = create_playlist(['Песня 1', 'Песня 2', 'Песня 3'])
        p.add_song('Новая')
        expected = ['Новая', 'Песня 1', 'Песня 2', 'Песня 3']
        for _ in range(8):
            p.next_song()
            self.assertEqual(p.songs.iter(), expected)
        self.assertEqual(p.current_song(), 'Новая')

    def test_restore_cursor(self):
        p = create_playlist(['А', 'Б'], 1)
        self.assertEqual(p.current_song(), 'Б')
        self.assertTrue(p.songs.validate())


if __name__ == '__main__':
    unittest.main()
