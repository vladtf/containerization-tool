import threading


class AtomicBoolean:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = False

    def get(self):
        with self._lock:
            return self._value

    def set(self, value):
        with self._lock:
            self._value = value

class ThreadTask:
    def __init__(self, name, target, args):
        self._name = name
        self._target = target
        self._args = args

    def get_name(self):
        return self._name

    def get_target(self):
        return self._target

    def get_args(self):
        return self._args

class ThreadPool:
    def __init__(self):
        self._threads = {}

    def add_thread(self, name, thread):
        self._threads[name] = thread

    def get_thread(self, name):
        return self._threads[name]

    def get_threads(self):
        return self._threads

    def stop_threads(self):
        for name, thread in self._threads.items():
            thread.join()
            print(f"Thread '{name}' stopped.")