import threading
import time

class Scheduler():
    def __init__(self):
        self.tasks = []
        self.lock = threading.Lock()
        self.alive = True


    def runPeriodically(self, period, task, args=()):
        t = threading.Timer(period, self.wrapper, (period, task, args))
        t.start()
        with self.lock:
            self.tasks.append(t)


    def runAfter(self, period, task, args=()):
        t = threading.Timer(period, task, args)
        t.start()
        with self.lock:
            self.tasks.append(t)

    def wrapper(self, period, task, args):
        if not self.alive: return

        self.pruneDeadTasks()
        task(*args)
        self.runPeriodically(period, task, args)


    def pruneDeadTasks(self):
        with self.lock:
            self.tasks = list(filter(lambda i:i.is_alive(), self.tasks))


    def kill(self):
        self.alive = False
        with self.lock:
            for i in self.tasks:
                i.cancel()
            self.tasks.clear()
