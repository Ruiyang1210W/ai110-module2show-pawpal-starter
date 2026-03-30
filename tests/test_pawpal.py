import pytest
from datetime import date, timedelta
from pawpal_system import CareTask, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(name="Morning Walk", duration=30, priority="high", category="walk"):
    return CareTask(name=name, duration_minutes=duration, priority=priority, category=category)


def make_owner_with_pet(available_minutes=60):
    owner = Owner(name="Test Owner", available_minutes=available_minutes)
    pet = Pet(name="Buddy", species="Dog", age=2)
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# CareTask tests
# ---------------------------------------------------------------------------

def test_mark_done_changes_status():
    """mark_done() should flip completed from False to True."""
    task = make_task()
    assert task.completed is False
    task.mark_done()
    assert task.completed is True


def test_mark_done_is_idempotent():
    """Calling mark_done() twice should not cause an error."""
    task = make_task()
    task.mark_done()
    task.mark_done()
    assert task.completed is True


def test_invalid_priority_raises():
    """Creating a task with a bad priority should raise ValueError."""
    with pytest.raises(ValueError):
        CareTask(name="Bad Task", duration_minutes=10, priority="urgent", category="walk")


def test_invalid_duration_raises():
    """Creating a task with zero or negative duration should raise ValueError."""
    with pytest.raises(ValueError):
        CareTask(name="Bad Task", duration_minutes=0, priority="high", category="walk")


def test_edit_updates_fields():
    """edit() should update only the fields that are passed."""
    task = make_task(name="Walk", duration=20, priority="low")
    task.edit(priority="high", duration_minutes=45)
    assert task.priority == "high"
    assert task.duration_minutes == 45
    assert task.name == "Walk"   # unchanged


def test_to_dict_returns_all_fields():
    """to_dict() should include all task fields."""
    task = make_task(name="Feed", duration=10, priority="medium", category="feeding")
    d = task.to_dict()
    assert d["name"] == "Feed"
    assert d["duration_minutes"] == 10
    assert d["priority"] == "medium"
    assert d["category"] == "feeding"
    assert d["completed"] is False


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Luna", species="Dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task())
    assert len(pet.get_tasks()) == 1


def test_add_multiple_tasks():
    """Adding three tasks should result in a task list of length three."""
    pet = Pet(name="Luna", species="Dog", age=3)
    for i in range(3):
        pet.add_task(make_task(name=f"Task {i}"))
    assert len(pet.get_tasks()) == 3


def test_remove_task_decreases_count():
    """remove_task() should drop the task from the pet's list."""
    pet = Pet(name="Luna", species="Dog", age=3)
    pet.add_task(make_task(name="Walk"))
    pet.remove_task("Walk")
    assert len(pet.get_tasks()) == 0


def test_get_pending_tasks_excludes_completed():
    """get_pending_tasks() should only return tasks that are not done."""
    pet = Pet(name="Luna", species="Dog", age=3)
    t1 = make_task(name="Walk")
    t2 = make_task(name="Feed")
    t1.mark_done()
    pet.add_task(t1)
    pet.add_task(t2)
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].name == "Feed"


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_owner_add_pet():
    """add_pet() should register the pet under the owner."""
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(Pet(name="Luna", species="Dog", age=3))
    assert len(owner.pets) == 1


def test_owner_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() should return tasks from every pet."""
    owner, pet1 = make_owner_with_pet()
    pet2 = Pet(name="Mochi", species="Cat", age=5)
    owner.add_pet(pet2)

    pet1.add_task(make_task(name="Walk"))
    pet2.add_task(make_task(name="Feed"))

    all_tasks = owner.get_all_tasks()
    task_names = [t.name for _, t in all_tasks]
    assert len(all_tasks) == 2
    assert "Walk" in task_names
    assert "Feed" in task_names


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_scheduler_high_priority_scheduled_first():
    """High-priority tasks should appear before lower-priority ones in the plan."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    pet.add_task(make_task(name="Low Task",  duration=10, priority="low"))
    pet.add_task(make_task(name="High Task", duration=10, priority="high"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    names = [t.name for _, t in plan]
    assert names.index("High Task") < names.index("Low Task")


def test_scheduler_skips_tasks_that_dont_fit():
    """Tasks that exceed available time should land in skipped_tasks."""
    owner, pet = make_owner_with_pet(available_minutes=20)
    pet.add_task(make_task(name="Short",  duration=10, priority="high"))
    pet.add_task(make_task(name="Long",   duration=60, priority="high"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    scheduled_names = [t.name for _, t in scheduler.scheduled_tasks]
    skipped_names   = [t.name for _, t in scheduler.skipped_tasks]
    assert "Short" in scheduled_names
    assert "Long"  in skipped_names


def test_scheduler_does_not_exceed_available_minutes():
    """Total scheduled time must never exceed owner's available_minutes."""
    owner, pet = make_owner_with_pet(available_minutes=40)
    for i in range(5):
        pet.add_task(make_task(name=f"Task {i}", duration=15, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    total = sum(t.duration_minutes for _, t in scheduler.scheduled_tasks)
    assert total <= owner.available_minutes


def test_scheduler_completed_tasks_are_excluded():
    """Already-completed tasks should not appear in the generated plan."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    done_task = make_task(name="Already Done", duration=10, priority="high")
    done_task.mark_done()
    pet.add_task(done_task)
    pet.add_task(make_task(name="Pending", duration=10, priority="high"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduled_names = [t.name for _, t in scheduler.scheduled_tasks]
    assert "Already Done" not in scheduled_names
    assert "Pending" in scheduled_names


# ---------------------------------------------------------------------------
# Edge cases — budget boundaries
# ---------------------------------------------------------------------------

def test_task_exactly_fills_budget_is_scheduled():
    """A task whose duration equals available_minutes exactly should be scheduled."""
    owner, pet = make_owner_with_pet(available_minutes=30)
    pet.add_task(make_task(name="Exact Fit", duration=30, priority="high"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduled_names = [t.name for _, t in scheduler.scheduled_tasks]
    assert "Exact Fit" in scheduled_names


def test_task_one_minute_over_budget_is_skipped():
    """A task that is one minute longer than the budget must be skipped."""
    owner, pet = make_owner_with_pet(available_minutes=30)
    pet.add_task(make_task(name="Too Long", duration=31, priority="high"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    skipped_names = [t.name for _, t in scheduler.skipped_tasks]
    assert "Too Long" in skipped_names


def test_owner_with_no_pets_returns_empty_plan():
    """An owner with no pets should produce an empty schedule without crashing."""
    owner = Owner(name="Empty", available_minutes=60)
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    assert plan == []


def test_pet_with_no_tasks_returns_empty_plan():
    """A pet with no tasks should produce an empty schedule without crashing."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    # pet has no tasks added
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    assert plan == []


def test_owner_with_zero_minutes_skips_all_tasks():
    """An owner with zero available minutes should skip every task."""
    owner, pet = make_owner_with_pet(available_minutes=0)
    pet.add_task(make_task(name="Walk", duration=10, priority="high"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    assert scheduler.scheduled_tasks == []
    assert len(scheduler.skipped_tasks) == 1


# ---------------------------------------------------------------------------
# Sorting tests
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should return tasks in ascending start_time order."""
    owner, pet = make_owner_with_pet(available_minutes=120)
    # Add tasks out of order (low priority schedules last = latest start time)
    pet.add_task(make_task(name="Late Task",  duration=10, priority="low"))
    pet.add_task(make_task(name="Early Task", duration=10, priority="high"))
    pet.add_task(make_task(name="Mid Task",   duration=10, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    sorted_plan = scheduler.sort_by_time()

    times = [task.start_time for _, task in sorted_plan]
    assert times == sorted(times), "sort_by_time() did not return tasks in ascending time order"


def test_sort_by_time_single_task():
    """sort_by_time() with one task should return a list of length one."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    pet.add_task(make_task(name="Only Task", duration=10, priority="high"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    assert len(scheduler.sort_by_time()) == 1


# ---------------------------------------------------------------------------
# Recurring task tests
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_occurrence_on_completion():
    """Completing a daily task should auto-create a new task due tomorrow."""
    owner, pet = make_owner_with_pet()
    pet.add_task(CareTask(name="Walk", duration_minutes=20, priority="high",
                          category="walk", frequency="daily"))
    pet.complete_task("Walk")

    future_tasks = [t for t in pet.tasks if not t.completed]
    assert len(future_tasks) == 1
    assert future_tasks[0].due_date == date.today() + timedelta(days=1)


def test_weekly_task_creates_next_occurrence_in_seven_days():
    """Completing a weekly task should auto-create a new task due in 7 days."""
    owner, pet = make_owner_with_pet()
    pet.add_task(CareTask(name="Bath", duration_minutes=30, priority="medium",
                          category="grooming", frequency="weekly"))
    pet.complete_task("Bath")

    future_tasks = [t for t in pet.tasks if not t.completed]
    assert len(future_tasks) == 1
    assert future_tasks[0].due_date == date.today() + timedelta(weeks=1)


def test_as_needed_task_creates_no_next_occurrence():
    """Completing an as-needed task should NOT create a new task."""
    owner, pet = make_owner_with_pet()
    pet.add_task(CareTask(name="Vet Visit", duration_minutes=60, priority="high",
                          category="meds", frequency="as-needed"))
    pet.complete_task("Vet Visit")

    all_tasks = pet.get_tasks()
    assert len(all_tasks) == 1           # only the completed original
    assert all_tasks[0].completed is True


def test_completing_task_twice_creates_only_one_future_task():
    """Calling complete_task() twice should not create two future occurrences."""
    owner, pet = make_owner_with_pet()
    pet.add_task(CareTask(name="Feed", duration_minutes=10, priority="high",
                          category="feeding", frequency="daily"))
    pet.complete_task("Feed")   # marks done, creates next
    pet.complete_task("Feed")   # tries again — original is already done, skipped

    future_tasks = [t for t in pet.tasks if not t.completed]
    assert len(future_tasks) == 1


def test_future_dated_task_not_included_in_todays_plan():
    """A task with a due_date in the future should be excluded from today's plan."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    future_task = CareTask(name="Future Walk", duration_minutes=20, priority="high",
                           category="walk", due_date=date.today() + timedelta(days=3))
    pet.add_task(future_task)

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduled_names = [t.name for _, t in scheduler.scheduled_tasks]
    assert "Future Walk" not in scheduled_names


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """Two tasks whose time windows overlap should produce a conflict warning."""
    owner, pet = make_owner_with_pet(available_minutes=120)
    pet.add_task(make_task(name="Task A", duration=30, priority="high"))
    pet.add_task(make_task(name="Task B", duration=30, priority="medium"))

    scheduler = Scheduler(owner)
    # Force both tasks to start at the same time
    scheduler.force_schedule("Buddy", "Task A", "09:00")
    scheduler.force_schedule("Buddy", "Task B", "09:15")  # starts inside Task A's window

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "Task A" in conflicts[0]
    assert "Task B" in conflicts[0]


def test_detect_conflicts_back_to_back_is_not_a_conflict():
    """Tasks that end and start at the same minute are NOT overlapping."""
    owner, pet = make_owner_with_pet(available_minutes=120)
    pet.add_task(make_task(name="Task A", duration=30, priority="high"))
    pet.add_task(make_task(name="Task B", duration=30, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.force_schedule("Buddy", "Task A", "09:00")  # ends 09:30
    scheduler.force_schedule("Buddy", "Task B", "09:30")  # starts exactly at 09:30

    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


def test_detect_conflicts_single_task_no_conflict():
    """A schedule with only one task can never have a conflict."""
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Only Task", duration=20, priority="high"))

    scheduler = Scheduler(owner)
    scheduler.force_schedule("Buddy", "Only Task", "08:00")

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_empty_schedule_no_crash():
    """detect_conflicts() on an empty schedule should return [] without error."""
    owner = Owner(name="Empty", available_minutes=60)
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


def test_no_conflicts_in_normal_generated_plan():
    """A plan generated by generate_plan() should never have time conflicts."""
    owner, pet = make_owner_with_pet(available_minutes=90)
    for i in range(4):
        pet.add_task(make_task(name=f"Task {i}", duration=15, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Filtering tests
# ---------------------------------------------------------------------------

def test_filter_by_pet_returns_correct_subset():
    """filter_by_pet() should return only tasks belonging to the named pet."""
    owner, pet1 = make_owner_with_pet(available_minutes=120)
    pet2 = Pet(name="Mochi", species="Cat", age=4)
    owner.add_pet(pet2)
    pet1.add_task(make_task(name="Dog Walk", duration=20, priority="high"))
    pet2.add_task(make_task(name="Cat Feed", duration=10, priority="high"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    buddy_tasks = scheduler.filter_by_pet("Buddy")
    assert all(pet.name == "Buddy" for pet, _ in buddy_tasks)
    assert len(buddy_tasks) == 1


def test_filter_by_pet_unknown_name_returns_empty():
    """filter_by_pet() with a non-existent name should return [] without crashing."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    pet.add_task(make_task())
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    assert scheduler.filter_by_pet("Ghost") == []


def test_filter_by_status_pending():
    """filter_by_status(False) should return only incomplete tasks."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    pet.add_task(make_task(name="Walk",  duration=10, priority="high"))
    pet.add_task(make_task(name="Feed",  duration=10, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduler.mark_task_done("Buddy", "Walk")

    pending = scheduler.filter_by_status(completed=False)
    names = [t.name for _, t in pending]
    assert "Walk" not in names
    assert "Feed" in names


def test_filter_by_status_nothing_done_returns_all():
    """filter_by_status(False) when nothing is done should return all scheduled tasks."""
    owner, pet = make_owner_with_pet(available_minutes=60)
    pet.add_task(make_task(name="Walk", duration=10, priority="high"))
    pet.add_task(make_task(name="Feed", duration=10, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.filter_by_status(completed=False)) == 2
