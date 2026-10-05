import tempfile
import unittest
from pathlib import Path
from rewards import Wallet, request

class RewardsTest(unittest.TestCase):
    def test_team_payment_carry_replay_and_isolated_pots(self):
        with tempfile.TemporaryDirectory() as tmp:
            wallet=Wallet(Path(tmp)/'test.sqlite3'); wallet.set('ana',0)
            def run(game,winners):
                begin=request(wallet,dict(game=game,action='begin',roster=['ana','bea']))
                payload=dict(game=game,action='finish',round=begin['round'],winners=winners)
                result=request(wallet,payload)
                self.assertEqual(request(wallet,payload),result)
                return result
            result=run('swimming',['ana','bea'])
            self.assertEqual(result,dict(paid={'ana':45},unpaid={'bea':45},carry=45))
            self.assertEqual(run('magikarp',['ana'])['paid'],{'ana':45})
            wallet.set('bea',0)
            self.assertEqual(run('swimming',['ana','bea'])['paid'],{'ana':68,'bea':67})
            self.assertEqual(wallet.balances(),{'ana':158,'bea':67})
    def test_invalid_winner_does_not_pay(self):
        with tempfile.TemporaryDirectory() as tmp:
            wallet=Wallet(Path(tmp)/'test.sqlite3'); wallet.set('ana',0)
            begin=request(wallet,dict(game='magikarp',action='begin',roster=['ana']))
            with self.assertRaises(ValueError):request(wallet,dict(game='magikarp',action='finish',round=begin['round'],winners=['outsider']))
            self.assertEqual(wallet.balances()['ana'],0)

if __name__=='__main__':unittest.main()
