"""Проверка работы сайта при отправке HTML-форм (требуется Flask)."""
import unittest
from app import app


class PlaylistSiteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['playlist_titles'] = ['Песня 1', 'Песня 2', 'Песня 3']
            session['playlist_cursor'] = 0

    def send(self, action, **fields):
        response = self.client.post('/playlist', data={'action': action, **fields})
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            return list(session['playlist_titles']), session['playlist_cursor']

    def test_cursor_moves_without_reordering(self):
        original = ['Песня 1', 'Песня 2', 'Песня 3']
        for action, expected_index in [
            ('playlist_next', 1), ('playlist_next', 2),
            ('playlist_next', 0), ('playlist_previous', 2),
            ('playlist_previous', 1),
        ]:
            titles, index = self.send(action)
            self.assertEqual(titles, original)
            self.assertEqual(index, expected_index)

    def test_add_to_front_and_remove_cursor(self):
        titles, index = self.send('playlist_add', title='Новая')
        self.assertEqual(titles, ['Новая', 'Песня 1', 'Песня 2', 'Песня 3'])
        self.assertEqual(index, 0)
        titles, index = self.send('playlist_next')
        self.assertEqual(titles, ['Новая', 'Песня 1', 'Песня 2', 'Песня 3'])
        self.assertEqual(index, 1)
        titles, index = self.send('playlist_remove')
        self.assertEqual(titles, ['Новая', 'Песня 2', 'Песня 3'])
        self.assertEqual(index, 1)


if __name__ == '__main__':
    unittest.main()
