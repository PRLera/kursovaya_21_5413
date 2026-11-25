import unittest
from app import app
from linked_list import DoublyLinkedList, CircularDoublyLinkedList


class NewFeaturesTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def post(self, action, **params):
        return self.client.post('/', data={'action': action, **params}, follow_redirects=True)

    def state(self):
        with self.client.session_transaction() as sess:
            return dict(sess)

    def test_no_wrap_from_last_in_doubly(self):
        self.post('choose_type', kind='doubly')
        self.post('next')
        self.post('next')
        response = self.post('next')
        self.assertIn('Переход к началу невозможен'.encode(), response.data)
        self.assertEqual(self.state()['cursor'], 2)

    def test_no_wrap_from_first_in_doubly(self):
        self.post('choose_type', kind='doubly')
        response = self.post('previous')
        self.assertIn('Переход к концу невозможен'.encode(), response.data)
        self.assertEqual(self.state().get('cursor', 0), 0)

    def test_left_shift(self):
        self.post('rotate', steps='1', direction='left')
        self.assertEqual(self.state()['values'], [20, 30, 10])

    def test_right_shift(self):
        self.post('rotate', steps='1', direction='right')
        self.assertEqual(self.state()['values'], [30, 10, 20])

    def test_multiple_right_steps(self):
        self.post('rotate', steps='2', direction='right')
        self.assertEqual(self.state()['values'], [20, 30, 10])

    def test_step_by_step(self):
        self.post('shift_start', steps='4', direction='left')
        self.assertEqual(self.state()['shift_steps'], 4)
        self.assertEqual(self.state()['values'], [10, 20, 30])
        self.post('shift_next')
        self.assertEqual(self.state()['values'], [20, 30, 10])
        self.assertEqual(self.state()['shift_steps'], 3)
        for _ in range(3):
            self.post('shift_next')
        self.assertEqual(self.state()['values'], [20, 30, 10])
        self.assertNotIn('shift_steps', self.state())

    def test_other_actions_blocked_during_step_mode(self):
        self.post('shift_start', steps='2', direction='right')
        response = self.post('add_back', value='15')
        self.assertIn('Сначала завершите'.encode(), response.data)
        self.assertEqual(self.state()['values'], [10, 20, 30])

    def test_cancel_preserves_completed_steps(self):
        self.post('shift_start', steps='2', direction='right')
        self.post('shift_next')
        self.post('shift_cancel')
        self.assertEqual(self.state()['values'], [30, 10, 20])
        self.assertNotIn('shift_steps', self.state())

    def test_cursor_moves_separately_from_head_shift(self):
        self.post('rotate', steps='1', direction='left')
        self.assertEqual(self.state()['values'], [20, 30, 10])
        self.assertEqual(self.state()['cursor'], 2)  # тот же узел 10

    def test_structure_invariants_after_rotations(self):
        ls = CircularDoublyLinkedList()
        for v in [10, 20, 30, 40]:
            ls.insert(ls.len(), v)
        ls.rotate(1, 'right')
        self.assertEqual(ls.iter(), [40, 10, 20, 30])
        self.assertTrue(ls.validate())
        ls.rotate(1, 'left')
        self.assertEqual(ls.iter(), [10, 20, 30, 40])
        self.assertTrue(ls.validate())

    def test_doubly_boundaries_raise(self):
        ls = DoublyLinkedList()
        for v in [1, 2]: ls.insert(ls.len(), v)
        with self.assertRaises(ValueError): ls.move_cursor(-1)
        ls.move_cursor(1)
        with self.assertRaises(ValueError): ls.move_cursor(1)
        self.assertEqual(ls.cursor.data, 2)


if __name__ == '__main__':
    unittest.main()
