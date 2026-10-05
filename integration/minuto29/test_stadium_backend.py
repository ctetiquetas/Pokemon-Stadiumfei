import threading
import time
import unittest
from stadium_backend import StadiumState


class StadiumTests(unittest.TestCase):
    def wait_until(self, predicate):
        deadline = time.monotonic() + 2
        while not predicate() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(predicate())

    def test_threshold_remainder_and_pause(self):
        pulses = []
        state = StadiumState(pulse=lambda hold: pulses.append(hold))
        state.likes(100)
        self.assertEqual(state.status()['pending'], 0)
        state.activate(True, 30, 60)
        state.likes(9)
        self.assertEqual(state.status()['remainder'], 9)
        self.assertEqual(pulses, [])
        state.likes(26)
        self.wait_until(lambda: state.status()['sent'] == 3)
        self.assertEqual(pulses, [30, 30, 30])
        self.assertEqual(state.status()['remainder'], 5)
        state.activate(False)
        self.assertEqual(state.status()['remainder'], 0)
        state.likes(10)
        self.assertEqual(state.status()['pending'], 0)

    def test_connection_failure_pauses_and_clears_queue(self):
        def fail(hold):
            raise ConnectionError('port cerrado')
        state = StadiumState(pulse=fail)
        state.activate(True)
        state.likes(35)
        self.wait_until(lambda: bool(state.status()['error']))
        info = state.status()
        self.assertFalse(info['armed'])
        self.assertEqual((info['pending'], info['remainder'], info['sent']), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
