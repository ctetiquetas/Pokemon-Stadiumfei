import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import canal29_chat as chat
from execution import ExecutionTracker
from queue_cancel import cancel_persisted

class ChatTest(unittest.TestCase):
    def test_aliases_persist_by_id_without_changing_old_events(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(chat,'SETTINGS',Path(tmp)/'settings.json'),patch.object(chat,'EVENTS',Path(tmp)/'events.jsonl'):
            chat.emit(kind='gift',gift='Maíz nuevo',gift_id=123)
            before=chat.EVENTS.read_bytes()
            chat.assign('Maíz nuevo',123,'corn')
            self.assertEqual(chat.effect('Nombre distinto',123),'corn')
            self.assertEqual(chat.effect('Maíz nuevo'),'corn')
            self.assertEqual(chat.EVENTS.read_bytes(),before)
            cleared=chat.clear();self.assertEqual(chat.read(chat.SETTINGS)['cleared_at'],cleared)
            self.assertLessEqual(json.loads(chat.EVENTS.read_text())['time'],cleared)
            self.assertEqual(chat.effect('Nombre distinto',123),'corn')
    def test_cleared_game_results_stay_hidden_in_new_tracker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);events=root/'tiktok-events.jsonl'
            events.write_text(json.dumps(dict(jobId='123'))+'\n')
            result=root/'tiktok-results.jsonl'
            result.write_text(json.dumps(dict(jobId='123',total=1,sequence=1,status='applied'))+'\n')
            cancel_persisted(events)
            tracker=ExecutionTracker();tracker.read(result)
            self.assertIn('123',tracker.dismissed)
            result.write_text(result.read_text()+json.dumps(dict(jobId='456',total=1,sequence=1,status='applied'))+'\n')
            tracker.read(result);self.assertNotIn('456',tracker.dismissed)

if __name__=='__main__':unittest.main()
