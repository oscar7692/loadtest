from datetime import datetime, timedelta
from dateutil import parser
from queue import Queue
from time import time, sleep
from threading import Thread
import json


# globals
json_log = []


class LoadTester:
    def __init__(self,
                 duration_time,
                 request_time,
                 worker,
                 n_jobs: int = 30,
                 count: int = 10):
        self.__count = count
        self.__d_time = datetime.now() + timedelta(minutes=int(duration_time)),
        self.__d_time = parser.parse(str(self.__d_time[0]))
        self.__n_jobs = n_jobs
        self.__q = Queue(self.__n_jobs * 2)
        self.__request_time = request_time
        self.__tasks_duration_per_iteration = 0
        self.__tasks_finished = 0
        self.__total_duration_per_task = 0
        self.__worker = worker

    def do_worker(self):
        while True:
            self.__q.get()

            start_thread_time = time()
            self.__worker()
            thread_duration = time() - start_thread_time

            self.__tasks_duration_per_iteration += thread_duration
            self.__tasks_finished += 1
            self.__q.task_done()

    def start(self):
        for i in range(self.__n_jobs):
            thread = Thread(target=self.do_worker)
            thread.daemon = True
            thread.name = f"t{i}"
            thread.start()

        start_program_time = time()
        iterations_count = 0
        try:
            print("starting iterations")
            while True:
                # counters
                iterations_count += 1
                self.__tasks_duration_per_iteration = 0

                # starting to count time of the iteration
                start_iteration_time = time()
                for i in range(self.__count):
                    self.__q.put((i, i))
                self.__q.join()

                iteration_duration = time() - start_iteration_time
                self.__total_duration_per_task += self.__tasks_duration_per_iteration

                print(f"iteration {iterations_count} finished in {iteration_duration:.2f}s, "
                      f"average thread duration is {self.__tasks_duration_per_iteration / self.__n_jobs:.2f}s, "
                      f"sum of thread durations is {self.__tasks_duration_per_iteration:.2f}s")

                request_data = {
                    "IterationNumber": f"{iterations_count}",
                    "Values": {
                        "RequestDone": f"{self.__count}",
                        "AverageDurationPerRequest": f"{iteration_duration:.2f}s",
                        "SumOfRequestDurations": f"{self.__tasks_duration_per_iteration:.2f}s"
                        }
                    }

                json_log.append(request_data)
                with open("request_log.json", "w+") as fl:
                    fl.write(json.dumps(json_log, indent=2))

                if self.__d_time < datetime.now():
                    raise KeyboardInterrupt
                sleep(self.__request_time)

        except KeyboardInterrupt:
            program_duration = time() - start_program_time
            average_task_duration = self.__total_duration_per_task / self.__tasks_finished \
                if self.__tasks_finished != 0 else 0
            print("Program finished. Results:")
            print(f"\tTotal time: {program_duration:.2f}s")
            print(f"\tTasks accomplished: {self.__tasks_finished}")
            print(f"\tAverage task duration: {average_task_duration:.2f}s")
