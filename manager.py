from heapq import heappush, heappop

from process import BackupProcess, ProcessStatus


class BackupManager:
    def __init__(self, bandwidth, starvation_limit):
        self.working_list = []
        self.waiting_list = []
        self.finished_list = []
        self.bandwidth = bandwidth
        self.starvation_limit = starvation_limit
        self.current_total_process_score = 0

    def check_for_finished_process(self):
        recently_finished = list(filter(lambda x: x.status == ProcessStatus.FINISHED, self.working_list))
        if recently_finished:
            self.finished_list.extend(recently_finished)
            self.working_list = list(filter(lambda x: x.status == ProcessStatus.RUNNING, self.working_list))

            self.update()

    def compute_bandwidth_for_each_process(self):
        self.current_total_process_score = sum(process.process_score for process in self.working_list)
        for process in self.working_list:
            speed = process.process_score / self.current_total_process_score * self.bandwidth

            if process.status == ProcessStatus.PENDING:
                process.start(speed)
            else:
                process.speed = speed

    def update(self):
        if not self.waiting_list:
            self.compute_bandwidth_for_each_process()
        else:
            no_process_is_starved = True
            while no_process_is_starved and len(self.waiting_list) > 0:
                process_score_list = [process.process_score for process in self.working_list]
                process_score_list.append(self.waiting_list[0].process_score)
                if min(process_score_list) / sum(process_score_list) * self.bandwidth < self.starvation_limit:
                    no_process_is_starved = False
                else:
                    self.working_list.append(heappop(self.waiting_list))
            self.compute_bandwidth_for_each_process()

    def add_new_process(self, process):
        heappush(self.waiting_list, process)
        self.update()

    def new_tick(self, timedelta):
        for process in self.working_list:
            process.update(timedelta)
        self.check_for_finished_process()
