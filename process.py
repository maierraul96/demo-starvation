from enum import Enum
from datetime import datetime
from time import sleep


class ProcessStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"


class BackupProcess:
    pid = 100

    def __init__(self, size, priority):
        self.pid = BackupProcess.pid
        BackupProcess.pid += 1
        self.status = ProcessStatus.PENDING
        self.speed = 0
        self.size = size
        self.transferred_size = 0
        self.priority = priority
        self.process_score = 9 - priority
        self.created_at = datetime.now()

    def __repr__(self):
        return f"PID: {self.pid}\tTransfered: {self.transferred_size:.2f}Mb/" \
               f"{self.size}Mb\tProgress: {self.compute_progress()}" \
               f"\tSpeed: {self.speed:.2f}Mb/s\tStatus: {self.status.value}"

    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        else:
            return self.created_at < other.created_at

    def __eq__(self, other):
        return self.priority == other.priority and self.created_at == other.created_at

    def compute_progress(self):
        percentage = int(self.transferred_size / self.size * 100)
        return "▮"*(percentage//5) + "▯"*((100-percentage)//5) + f" {percentage}%"

    def start(self, speed):
        self.status = ProcessStatus.RUNNING
        self.speed = speed

    def update(self, timedelta):
        # Update transferred size
        self.transferred_size += timedelta.total_seconds() * self.speed

        # Update status
        if self.transferred_size >= self.size:
            self.finished()

    def finished(self):
        self.status = ProcessStatus.FINISHED
        self.transferred_size = self.size
        self.speed = 0
