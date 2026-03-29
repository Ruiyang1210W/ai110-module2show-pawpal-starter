from pawpal_system import CareTask, Pet, Owner, Scheduler


# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

# Pet 1
luna = Pet(name="Luna", species="Dog", age=3)
luna.add_task(CareTask(name="Morning Walk",    duration_minutes=30, priority="high",   category="walk"))
luna.add_task(CareTask(name="Breakfast",       duration_minutes=10, priority="high",   category="feeding"))
luna.add_task(CareTask(name="Brush Coat",      duration_minutes=15, priority="low",    category="grooming"))

# Pet 2
mochi = Pet(name="Mochi", species="Cat", age=5)
mochi.add_task(CareTask(name="Wet Food",       duration_minutes=5,  priority="high",   category="feeding"))
mochi.add_task(CareTask(name="Flea Medication",duration_minutes=5,  priority="medium", category="meds",    frequency="weekly"))
mochi.add_task(CareTask(name="Laser Play",     duration_minutes=20, priority="low",    category="enrichment"))

owner.add_pet(luna)
owner.add_pet(mochi)

# --- Generate plan ---
scheduler = Scheduler(owner)
scheduler.generate_plan()

# --- Print Today's Schedule ---
PRIORITY_COLORS = {"high": "!!!", "medium": ">> ", "low": "   "}

def print_schedule(scheduler: Scheduler) -> None:
    owner = scheduler.owner
    total_scheduled = sum(t.duration_minutes for _, t in scheduler.scheduled_tasks)

    print("=" * 50)
    print(f"  TODAY'S SCHEDULE  //  {owner.name}")
    print(f"  Time budget: {owner.available_minutes} min  |  Used: {total_scheduled} min")
    print("=" * 50)

    if scheduler.scheduled_tasks:
        print("\n  PLANNED TASKS\n")
        for i, (pet, task) in enumerate(scheduler.scheduled_tasks, start=1):
            marker = PRIORITY_COLORS.get(task.priority, "   ")
            print(f"  {i}. {marker} {task.name}")
            print(f"       Pet      : {pet.name} ({pet.species})")
            print(f"       Category : {task.category}  |  {task.duration_minutes} min  |  Priority: {task.priority}")
            print()

    if scheduler.skipped_tasks:
        print("  SKIPPED (not enough time)\n")
        for pet, task in scheduler.skipped_tasks:
            print(f"  x  {task.name} for {pet.name} — needs {task.duration_minutes} min")
        print()

    print("=" * 50)
    print(scheduler.explain_plan())
    print("=" * 50)


print_schedule(scheduler)
