from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple

DAY_START_HOUR = 8   # schedule begins at 08:00 by default


# ---------------------------------------------------------------------------
# CareTask
# ---------------------------------------------------------------------------

@dataclass
class CareTask:
    """A single pet care activity."""

    VALID_PRIORITIES = ("high", "medium", "low")
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    name: str
    duration_minutes: int
    priority: str           # "high", "medium", or "low"
    category: str           # e.g. "walk", "feeding", "meds", "grooming"
    frequency: str = "daily"              # "daily", "weekly", or "as-needed"
    completed: bool = False
    start_time: str = ""                  # "HH:MM" — assigned by Scheduler.generate_plan()
    due_date: date = field(default_factory=date.today)  # next date this task should appear

    def __post_init__(self):
        """Validate priority and duration immediately after construction."""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"priority must be one of {self.VALID_PRIORITIES}, got '{self.priority}'"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

    def mark_done(self) -> Optional["CareTask"]:
        """
        Mark this task complete and return the next occurrence if recurring.

        Returns a new CareTask (due tomorrow for daily, +7 days for weekly)
        or None for as-needed tasks. The caller is responsible for storing it.
        """
        self.completed = True

        if self.frequency == "daily":
            next_due = date.today() + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = date.today() + timedelta(weeks=1)
        else:
            return None   # "as-needed" — no automatic next occurrence

        return CareTask(
            name=self.name,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            due_date=next_due,
        )

    def edit(
        self,
        name: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> None:
        """Update any combination of task fields."""
        if name is not None:
            self.name = name
        if duration_minutes is not None:
            if duration_minutes <= 0:
                raise ValueError("duration_minutes must be a positive integer")
            self.duration_minutes = duration_minutes
        if priority is not None:
            if priority not in self.VALID_PRIORITIES:
                raise ValueError(
                    f"priority must be one of {self.VALID_PRIORITIES}, got '{priority}'"
                )
            self.priority = priority
        if category is not None:
            self.category = category
        if frequency is not None:
            self.frequency = frequency

    def to_dict(self) -> dict:
        """Return a plain dictionary representation of this task."""
        return {
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "frequency": self.frequency,
            "completed": self.completed,
            "start_time": self.start_time,
            "due_date": self.due_date.isoformat(),
        }


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet with its own list of care tasks."""

    name: str
    species: str
    age: int
    notes: str = ""
    tasks: List[CareTask] = field(default_factory=list)

    def summary(self) -> str:
        """Return a short human-readable description of the pet."""
        return f"{self.name} ({self.species}, age {self.age})"

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name. Does nothing if the task is not found."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_tasks(self) -> List[CareTask]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[CareTask]:
        """Return only tasks that have not been completed yet."""
        return [t for t in self.tasks if not t.completed]

    def complete_task(self, task_name: str) -> bool:
        """
        Mark a task done by name and auto-append the next occurrence if recurring.

        Uses timedelta internally via CareTask.mark_done():
          - daily  -> due_date = today + timedelta(days=1)
          - weekly -> due_date = today + timedelta(weeks=1)
          - as-needed -> no new task created

        Returns True if the task was found, False otherwise.
        """
        for task in self.tasks:
            if task.name == task_name and not task.completed:
                next_task = task.mark_done()   # returns new CareTask or None
                if next_task is not None:
                    self.tasks.append(next_task)
                return True
        return False


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """A pet owner who may have one or more pets."""

    def __init__(self, name: str, available_minutes: int, preferences: str = ""):
        """Create an owner with a daily time budget and an empty pet list."""
        if available_minutes < 0:
            raise ValueError("available_minutes cannot be negative")
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name. Does nothing if not found."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return the Pet object with the given name, or None."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Tuple[Pet, CareTask]]:
        """Return every (pet, task) pair across all pets for the Scheduler to consume."""
        pairs = []
        for pet in self.pets:
            for task in pet.get_tasks():
                pairs.append((pet, task))
        return pairs

    def get_all_pending_tasks(self) -> List[Tuple[Pet, CareTask]]:
        """Return only (pet, task) pairs where the task is not yet completed."""
        return [(pet, task) for pet, task in self.get_all_tasks() if not task.completed]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Builds a daily care plan from the owner's available time and pet tasks.

    Flow:
        1. Call generate_plan() to populate scheduled_tasks and skipped_tasks.
        2. Call explain_plan() for a human-readable breakdown.
        3. Call get_plan() any time afterwards to retrieve the scheduled list.
    """

    def __init__(self, owner: Owner):
        """Attach the scheduler to an owner; plan lists start empty."""
        self.owner = owner
        self.scheduled_tasks: List[Tuple[Pet, CareTask]] = []
        self.skipped_tasks: List[Tuple[Pet, CareTask]] = []

    def generate_plan(self) -> List[Tuple[Pet, CareTask]]:
        """Sort pending due tasks by priority, fit them into available time, and assign start times."""
        today = date.today()
        # Only include tasks that are pending AND due today or overdue
        pending = [
            (pet, task) for pet, task in self.owner.get_all_pending_tasks()
            if task.due_date <= today
        ]

        # Sort by priority order, then by duration (shorter first as a tiebreaker)
        pending.sort(key=lambda pair: (
            CareTask.PRIORITY_ORDER[pair[1].priority],
            pair[1].duration_minutes,
        ))

        self.scheduled_tasks = []
        self.skipped_tasks = []
        time_remaining = self.owner.available_minutes
        elapsed_minutes = DAY_START_HOUR * 60   # running clock starting at 08:00

        for pet, task in pending:
            if task.duration_minutes <= time_remaining:
                # Assign "HH:MM" start time from the running clock
                hh, mm = divmod(elapsed_minutes, 60)
                task.start_time = f"{hh:02d}:{mm:02d}"
                self.scheduled_tasks.append((pet, task))
                time_remaining -= task.duration_minutes
                elapsed_minutes += task.duration_minutes
            else:
                task.start_time = ""
                self.skipped_tasks.append((pet, task))

        return self.scheduled_tasks

    @staticmethod
    def _hhmm_to_minutes(hhmm: str) -> int:
        """Convert a 'HH:MM' string to total minutes since midnight."""
        h, m = map(int, hhmm.split(":"))
        return h * 60 + m

    def force_schedule(self, pet_name: str, task_name: str, start_time: str) -> bool:
        """
        Manually place a task into scheduled_tasks at a specific 'HH:MM' start time.
        Useful for testing conflict detection. Returns False if the task is not found.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.name == task_name:
                task.start_time = start_time
                self.scheduled_tasks.append((pet, task))
                return True
        return False

    def detect_conflicts(self) -> List[str]:
        """
        Check all scheduled tasks for time window overlaps.

        Strategy: for every pair of tasks, if one starts before the other ends
        (and vice versa), that is a conflict. Returns a list of warning strings
        rather than raising an exception so the app can show them without crashing.
        """
        warnings = []
        tasks_with_times = [
            (pet, task) for pet, task in self.scheduled_tasks
            if task.start_time
        ]

        for i in range(len(tasks_with_times)):
            for j in range(i + 1, len(tasks_with_times)):
                pet_a, task_a = tasks_with_times[i]
                pet_b, task_b = tasks_with_times[j]

                a_start = self._hhmm_to_minutes(task_a.start_time)
                a_end   = a_start + task_a.duration_minutes
                b_start = self._hhmm_to_minutes(task_b.start_time)
                b_end   = b_start + task_b.duration_minutes

                # Overlap when one window starts before the other ends
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"CONFLICT: '{task_a.name}' ({pet_a.name}, "
                        f"{task_a.start_time}-{a_end // 60:02d}:{a_end % 60:02d}) "
                        f"overlaps with '{task_b.name}' ({pet_b.name}, "
                        f"{task_b.start_time}-{b_end // 60:02d}:{b_end % 60:02d})"
                    )

        return warnings

    def sort_by_time(self) -> List[Tuple[Pet, CareTask]]:
        """Return scheduled tasks sorted by start_time (HH:MM) using a lambda key."""
        return sorted(
            self.scheduled_tasks,
            key=lambda pair: (
                int(pair[1].start_time[:2]) * 60 + int(pair[1].start_time[3:])
                if pair[1].start_time else 0
            ),
        )

    def filter_by_pet(self, pet_name: str) -> List[Tuple[Pet, CareTask]]:
        """Return scheduled tasks belonging to the named pet only."""
        return [(pet, task) for pet, task in self.scheduled_tasks if pet.name == pet_name]

    def filter_by_status(self, completed: bool) -> List[Tuple[Pet, CareTask]]:
        """Return scheduled tasks matching the given completion status."""
        return [(pet, task) for pet, task in self.scheduled_tasks if task.completed == completed]

    def explain_plan(self) -> str:
        """Return a plain-English summary of scheduled and skipped tasks; call generate_plan() first."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No plan generated yet. Call generate_plan() first."

        lines = []
        total = sum(t.duration_minutes for _, t in self.scheduled_tasks)
        lines.append(
            f"Daily plan for {self.owner.name} "
            f"({total} of {self.owner.available_minutes} minutes used)\n"
        )

        if self.scheduled_tasks:
            lines.append("Scheduled:")
            for pet, task in self.scheduled_tasks:
                lines.append(
                    f"  + [{task.priority.upper()}] {task.name} "
                    f"for {pet.name} -{task.duration_minutes} min"
                )

        if self.skipped_tasks:
            lines.append("\nSkipped (not enough time remaining):")
            for pet, task in self.skipped_tasks:
                lines.append(
                    f"  - [{task.priority.upper()}] {task.name} "
                    f"for {pet.name} -needs {task.duration_minutes} min"
                )

        return "\n".join(lines)

    def get_plan(self) -> List[Tuple[Pet, CareTask]]:
        """Return the scheduled tasks from the last generate_plan() call."""
        return self.scheduled_tasks

    def mark_task_done(self, pet_name: str, task_name: str) -> bool:
        """
        Mark a task done and auto-schedule its next occurrence if recurring.
        Delegates to Pet.complete_task() which handles the timedelta logic.
        Returns True if the task was found and marked, False otherwise.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        return pet.complete_task(task_name)
