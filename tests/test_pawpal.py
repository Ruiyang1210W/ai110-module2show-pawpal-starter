import pytest
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
