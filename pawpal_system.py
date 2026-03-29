from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pet:
    name: str
    species: str
    age: int
    notes: str = ""

    def summary(self) -> str:
        pass


@dataclass
class CareTask:
    name: str
    duration_minutes: int
    priority: str          # "high", "medium", or "low"
    category: str          # e.g. "walk", "feeding", "meds", "grooming"
    completed: bool = False

    def mark_done(self) -> None:
        pass

    def edit(self, duration_minutes: Optional[int] = None, priority: Optional[str] = None) -> None:
        pass

    def to_dict(self) -> dict:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: str = ""):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pet: Optional[Pet] = None
        self.tasks: List[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        pass

    def remove_task(self, task_name: str) -> None:
        pass

    def get_tasks(self) -> List[CareTask]:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_tasks: List[CareTask] = []
        self.skipped_tasks: List[CareTask] = []

    def generate_plan(self) -> None:
        pass

    def explain_plan(self) -> str:
        pass

    def get_plan(self) -> List[CareTask]:
        pass
