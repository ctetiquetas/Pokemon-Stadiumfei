"""Immediate gift delivery and cumulative TikTok streak deltas."""
class GiftDelivery:
    def __init__(self):self.streaks={};self.seen=set()
    def delta(self,user,gift_id,count,streakable,streaking,message_id=''):
        token=f'{message_id}:{count}:{bool(streaking)}' if message_id else ''
        if token and token in self.seen:return 0
        if token:self.seen.add(token)
        if len(self.seen)>10000:self.seen={token}
        count=max(1,int(count));key=(user,str(gift_id))
        if not streakable:return count
        previous=self.streaks.get(key,0)
        delta=count-previous if count>=previous else count
        if streaking:self.streaks[key]=count
        else:self.streaks.pop(key,None)
        return delta
