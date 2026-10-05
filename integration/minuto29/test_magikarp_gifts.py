import asyncio,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
import app

class BridgeGiftTest(unittest.TestCase):
    def test_live_streak_applies_before_completion_and_avoids_other_game_queue(self):
        class Client:
            def __init__(self,**kwargs):self.handlers={}
            def on(self,kind):
                def register(fn):self.handlers[kind]=fn;return fn
                return register
            def run(self,**kwargs):
                async def scenario():
                    for count,streaking,msg in [(1,True,1),(2,True,1),(2,False,2)]:
                        await self.handlers[app.GiftEvent](SimpleNamespace(user=SimpleNamespace(display_id='ana',nickname='Ana'),gift=SimpleNamespace(type=1,name='Rose',id=99,diamond_count=0),repeat_count=count,streaking=streaking,common=SimpleNamespace(msg_id=msg)))
                asyncio.run(scenario())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mapping=root/'mapping.json';mapping.write_text('{}')
            with patch.object(app,'TikTokLiveClient',Client),patch.object(app.canal29_chat,'mode',return_value=''),patch.object(app.canal29_chat,'emit'),patch.object(app,'magikarp_active',return_value=True),patch.object(app,'magikarp_post',return_value=dict(assigned=True,applied=True,status='Rosa → salto extra aplicado')) as post,patch.object(app,'pokemon_forward') as other:
                app.bridge_main('test',str(root/'out.jsonl'),str(mapping),str(root/'status.jsonl'),str(root/'wallet.db'))
            self.assertEqual(post.call_count,2);other.assert_not_called()
            self.assertEqual([c.args[1]['count'] for c in post.call_args_list],[1,1])
            events=[json.loads(line) for line in (root/'status.jsonl').read_text(encoding='utf-8').splitlines()]
            effects=[e for e in events if e['type']=='magikarp_gift']
            self.assertEqual(len(effects),2);self.assertTrue(all(e['applied'] for e in effects))
            self.assertFalse(any(e['type']=='queued' for e in events))
    def test_queue_displays_received_id_and_assignment_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            status=Path(tmp)/'status.jsonl'
            status.write_text(json.dumps(dict(type='magikarp_gift',sender='Ana',gift='Rose',gift_id=99,count=1,assigned=True,applied=True,message='Rosa → salto extra aplicado'))+'\n')
            ui=SimpleNamespace(status_file=status,status_offset=0,queue_tree=Mock(),add_chat_line=Mock())
            app.TikTokGiftApp.read_status_events(ui)
            values=ui.queue_tree.insert.call_args.kwargs['values']
            self.assertEqual(values,('Ana','Rose ×1 · ID 99','Rosa → salto extra aplicado'))

if __name__=='__main__':unittest.main()
