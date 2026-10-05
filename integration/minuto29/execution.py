"""Read game acknowledgements. Writing to the queue is not execution."""
import json


class ExecutionTracker:
    def __init__(self):
        self.offset = 0
        self.path = None
        self.jobs = {}
        self.dismissed = set()

    def register(self, job_id, total, sender='', gift=''):
        job = self.jobs.setdefault(str(job_id), dict(total=total, sender=sender, gift=gift,
                                                     applied=set(), failed=set(), cancelled=set()))
        job['total'] = max(job['total'], total)
        return job

    def read(self, path):
        changed = set()
        if path != self.path:
            self.path, self.offset = path, 0
        if not path.exists(): return changed
        if path.stat().st_size < self.offset: self.offset = 0
        with path.open('rb') as stream:
            stream.seek(self.offset)
            while True:
                line = stream.readline()
                if not line.endswith(b'\n'): break
                self.offset = stream.tell()
                try:
                    event = json.loads(line)
                    job_id = str(event['jobId'])
                    if path.with_name('tiktok-cancellations').joinpath(job_id+'.cancel').is_file():
                        self.dismissed.add(job_id)
                    state = event['status']
                    if state not in ('applied', 'failed', 'cancelled'): continue
                    job = self.register(job_id, int(event['total']), event.get('sender','TikTok'), event.get('gift',''))
                    sequence = int(event['sequence'])
                    if not 1 <= sequence <= job['total']: continue
                    if any(sequence in job[k] for k in ('applied','failed','cancelled')): continue
                    job[state].add(sequence)
                    changed.add(job_id)
                except (ValueError, KeyError, TypeError):
                    continue
        return changed

    def label(self, job_id):
        job = self.jobs[str(job_id)]
        applied, failed, cancelled = (len(job[k]) for k in ('applied','failed','cancelled'))
        pending = max(0, job['total']-applied-failed-cancelled)
        suffix = f' · Fallidos: {failed}' if failed else ''
        suffix += f' · Cancelados: {cancelled}' if cancelled else ''
        return f"Aplicados: {applied}/{job['total']} · Faltan: {pending}{suffix}"
