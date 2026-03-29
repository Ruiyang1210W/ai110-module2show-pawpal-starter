from dataclasses import dataclass, field
from typing import List, Optional, Tuple


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
    frequency: str = "daily"  # e.g. "daily", "weekly", "as-needed"
    completed: bool = False

    def __post_init__(self):
        """Validate priority and duration immediately after construction."""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"priority must be one of {self.VALID_PRIORITIES}, got '{self.priority}'"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.completed = True

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
        """Sort pending tasks by priority and greedily fit them into the owner's available time."""
        pending = self.owner.get_all_pending_tasks()

        # Sort by priority order, then by duration (shorter first as a tiebreaker)
        pending.sort(key=lambda pair: (
            CareTask.PRIORITY_ORDER[pair[1].priority],
            pair[1].duration_minutes,
        ))

        self.scheduled_tasks = []
        self.skipped_tasks = []
        time_remaining = self.owner.available_minutes

        for pet, task in pending:
            if task.duration_minutes <= time_remaining:
                self.scheduled_tasks.append((pet, task))
                time_remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append((pet, task))

        return self.scheduled_tasks

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
        Mark a specific task as completed during the day.
        Returns True if found and marked, False otherwise.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.name == task_name:
                task.mark_done()
                return True
        return False
