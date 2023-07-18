import logging
import threading
import time

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class AtomicBoolean:
    def __init__(self, value):
        self._lock = threading.Lock()
        self._value = value

    def get(self):
        with self._lock:
            return self._value

    def set(self, value):
        with self._lock:
            self._value = value


class Task:
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

    def task_wrapper(self, is_running: AtomicBoolean):
        while is_running.get():
            self._target(*self._args)

        logger.info("Thread '%s' stopped", self._name)

    def build_thread(self, is_running: AtomicBoolean):
        return threading.Thread(target=self.task_wrapper, args=(is_running,))


class ThreadPool:
    def __init__(self, monitor_interval):
        self._threads: dict[str, threading.Thread] = {}
        self._tasks: dict[str, Task] = {}
        self._monitor_interval = monitor_interval
        self._threads_running = AtomicBoolean(True)

    def add_task(self, name, target, args):
        self._tasks[name] = Task(name, target, args)

    def start_threads(self):
        for task_name, task in self._tasks.items():
            self._threads[task_name] = task.build_thread(self._threads_running)
            self._threads[task_name].start()

    def stop_threads(self):
        self._threads_running.set(False)

        for thread_name, thread in self._threads.items():
            logger.info("Stopping thread '%s'...", thread_name)
            thread.join()

        logger.info("All threads stopped")

    def monitor_threads(self):
        try:
            while self._threads_running.get():
                for thread_name, thread in self._threads.items():
                    if not thread.is_alive():
                        logger.info("Thread '%s' is not alive. Restarting...", thread_name)

                        self._threads[thread_name] = self._tasks[thread_name].build_thread(self._threads_running)
                        self._threads[thread_name].start()

                time.sleep(self._monitor_interval)
        except KeyboardInterrupt:
            logger.info("Interrupt signal received. Stopping application...")
            self.stop_threads()
