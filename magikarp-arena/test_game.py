import unittest
from game import Arena

class Clock:
    now=0
    def __call__(self):return self.now

class ArenaTests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.game=Arena(self.clock)
    def join(self,user='uno',**data):self.game.event(dict(kind='comment',user=user,message='!unir',**data))
    def taps(self,user,count):self.game.event(dict(kind='like',user=user,count=count))
    def begin(self,duration=60):self.game.start(duration);self.clock.now=3;self.game.tick()
    def test_limit_identity_duplicates_and_late_join(self):
        self.join('@UNO',name='<script>');self.join('uno')
        for i in range(20):self.join(str(i))
        self.assertEqual(len(self.game.players),12)
        self.assertEqual(len(set(p['color'] for p in self.game.players.values())),12)
        self.begin();self.join('tarde');self.assertNotIn('tarde',self.game.players)
    def test_individual_remainder_hit_and_ignored_users(self):
        self.join('uno');self.join('dos');self.taps('uno',100);self.begin()
        self.taps('uno',9);self.taps('dos',1)
        self.assertEqual(self.game.players['uno']['remainder'],9)
        self.taps('uno',1)
        self.assertEqual(self.game.players['uno']['score'],0)
        self.clock.now=3.35;self.game.tick()
        self.assertEqual(self.game.players['uno']['score'],1)
        self.assertEqual(self.game.players['dos']['score'],0)
        self.taps('unknown',100);self.taps('',20)
        self.assertEqual(self.game.unattributed,20)
        self.assertEqual(len(self.game.players),2)
    def test_queue_scores_at_collisions_even_after_delayed_tick(self):
        self.join();self.begin();self.taps('uno',35)
        self.clock.now=5.6;self.game.tick()
        self.assertEqual(self.game.players['uno']['score'],3)
        self.assertEqual(self.game.players['uno']['remainder'],5)
    def test_deadline_winner_no_scores_after_round_and_reset(self):
        self.join('uno');self.join('dos');self.begin(10)
        self.clock.now=12.9;self.taps('uno',100)
        self.clock.now=14;state=self.game.snapshot()
        self.assertEqual(state['phase'],'finished')
        self.assertEqual([p['score'] for p in state['players']],[0,0])
        self.assertEqual(state['winners'],['uno','dos'])
        self.taps('dos',100);self.assertEqual(self.game.players['dos']['pending'],0)
        self.game.new_room();self.assertEqual(self.game.snapshot()['players'],[])
    def test_unique_winner_and_inflight_queue_cancelled(self):
        self.join('uno');self.join('dos');self.begin();self.taps('uno',30)
        self.clock.now=3.5;self.game.finish()
        state=self.game.snapshot();self.assertEqual(state['winners'],['uno'])
        self.assertEqual(state['players'][0]['pending'],0)
        self.clock.now=10;self.assertEqual(self.game.snapshot()['players'][0]['score'],1)

if __name__=='__main__':unittest.main()
