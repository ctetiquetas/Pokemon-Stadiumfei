import sys
import unittest
from pathlib import Path
from game import Arena,HIT_SECONDS
sys.path.insert(0,str(Path.home()/'Documents/GitHub/Shipwright/tools/tiktok-live-bridge'))
from magikarp_gifts import GiftDelivery

class GiftTests(unittest.TestCase):
    def setUp(self):
        self.now=0
        self.arena=Arena(clock=lambda:self.now)
        self.arena.event(dict(kind='comment',user='ana',message='!unir'))
    def start(self):self.arena.start();self.now=3;self.arena.tick()
    def gift(self,name,user='ana',**extra):return self.arena.event(dict(kind='gift',gift=name,user=user,**extra))
    def test_no_stock_unassigned_and_absent_player(self):
        self.assertFalse(self.gift('Rose')['applied'])
        self.start()
        self.assertFalse(self.gift('Go Popular')['assigned'])
        self.assertFalse(self.gift('Rose',user='absent')['applied'])
        self.assertEqual(self.arena.players['ana']['gift_hits'],[])
    def test_rose_immediate_animation_points_on_collision_and_dedup(self):
        self.start();self.assertTrue(self.gift('Rose',event_id='one')['applied'])
        self.assertEqual(self.arena.snapshot()['players'][0]['gift_jump_age'],0)
        self.assertEqual(self.arena.players['ana']['score'],0)
        self.gift('Rose',event_id='one')
        self.now+=HIT_SECONDS+.01;self.arena.tick()
        self.assertEqual(self.arena.players['ana']['score'],1)
        self.assertEqual(self.arena.players['ana']['pending'],0)
    def test_corn_refresh_without_stacking_and_normal_points_after_expiry(self):
        self.start();self.gift('Its corn');self.assertEqual(self.arena.players['ana']['double_until'],11)
        self.gift('Its corn',count=10);self.assertEqual(self.arena.players['ana']['double_until'],11)
        self.gift('Rose');self.now=3.5;self.arena.tick();self.assertEqual(self.arena.players['ana']['score'],2)
        self.now=12;self.gift('Rose');self.now=12.5;self.arena.tick();self.assertEqual(self.arena.players['ana']['score'],3)
        self.assertFalse(self.arena.snapshot()['players'][0]['double_remaining'])
    def test_streak_processed_live_without_final_duplicate(self):
        delivery=GiftDelivery()
        self.assertEqual([delivery.delta('ana',1,n,True,ongoing,token) for n,ongoing,token in [(1,True,10),(2,True,10),(2,False,11),(2,False,11),(1,False,12)]],[1,1,0,0,1])

if __name__=='__main__':unittest.main()
