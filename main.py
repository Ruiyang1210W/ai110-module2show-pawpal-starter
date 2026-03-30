from pawpal_system import CareTask, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=90)

luna = Pet(name="Luna", species="Dog", age=3)
luna.add_task(CareTask(name="Morning Walk",     duration_minutes=30, priority="high",   category="walk"))
luna.add_task(CareTask(name="Breakfast",        duration_minutes=10, priority="high",   category="feeding"))
luna.add_task(CareTask(name="Brush Coat",       duration_minutes=15, priority="low",    category="grooming"))

mochi = Pet(name="Mochi", species="Cat", age=5)
mochi.add_task(CareTask(name="Wet Food",        duration_minutes=5,  priority="high",   category="feeding"))
mochi.add_task(CareTask(name="Flea Medication", duration_minutes=5,  priority="medium", category="meds",        frequency="weekly"))
mochi.add_task(CareTask(name="Laser Play",      duration_minutes=20, priority="low",    category="enrichment"))

owner.add_pet(luna)
owner.add_pet(mochi)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def print_conflicts(label: str, conflicts: list) -> None:
    print(f"\n  [{label}]")
    if not conflicts:
        print("  No conflicts detected. All clear!")
    else:
        for w in conflicts:
            print(f"  WARNING: {w}")


# ---------------------------------------------------------------------------
# Case 1: Normal generated plan — should have zero conflicts
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  CASE 1: Normal generated plan (sequential, no conflicts)")
print("=" * 60)

scheduler = Scheduler(owner)
scheduler.generate_plan()

print("\n  Scheduled tasks:")
for pet, task in scheduler.sort_by_time():
    end_min = Scheduler._hhmm_to_minutes(task.start_time) + task.duration_minutes
    end_str = f"{end_min // 60:02d}:{end_min % 60:02d}"
    print(f"    {task.start_time}-{end_str}  {task.name:<22} ({pet.name})")

print_conflicts("Conflict check", scheduler.detect_conflicts())


# ---------------------------------------------------------------------------
# Case 2: Force two tasks to overlap — conflict must be detected
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  CASE 2: Two tasks force-scheduled at the same time")
print("=" * 60)

# Add two extra tasks and manually place them at overlapping windows
luna.add_task(CareTask(name="Vet Medication",   duration_minutes=20, priority="high", category="meds"))
mochi.add_task(CareTask(name="Morning Stretch", duration_minutes=15, priority="medium", category="enrichment"))

scheduler2 = Scheduler(owner)
# Force both tasks to start at 09:00 — they will overlap
scheduler2.force_schedule("Luna",  "Vet Medication",   "09:00")
scheduler2.force_schedule("Mochi", "Morning Stretch",  "09:05")

print("\n  Force-scheduled tasks:")
for pet, task in scheduler2.scheduled_tasks:
    end_min = Scheduler._hhmm_to_minutes(task.start_time) + task.duration_minutes
    end_str = f"{end_min // 60:02d}:{end_min % 60:02d}"
    print(f"    {task.start_time}-{end_str}  {task.name:<22} ({pet.name})")

print_conflicts("Conflict check", scheduler2.detect_conflicts())


# ---------------------------------------------------------------------------
# Case 3: Same pet, back-to-back but NOT overlapping — should be clean
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  CASE 3: Back-to-back tasks (touching but not overlapping)")
print("=" * 60)

luna.add_task(CareTask(name="Cool Down Walk",   duration_minutes=10, priority="low", category="walk"))
luna.add_task(CareTask(name="Post Walk Feed",   duration_minutes=10, priority="low", category="feeding"))

scheduler3 = Scheduler(owner)
scheduler3.force_schedule("Luna", "Cool Down Walk", "10:00")   # ends 10:10
scheduler3.force_schedule("Luna", "Post Walk Feed", "10:10")   # starts exactly when previous ends

print("\n  Force-scheduled tasks:")
for pet, task in scheduler3.scheduled_tasks:
    end_min = Scheduler._hhmm_to_minutes(task.start_time) + task.duration_minutes
    end_str = f"{end_min // 60:02d}:{end_min % 60:02d}"
    print(f"    {task.start_time}-{end_str}  {task.name:<22} ({pet.name})")

print_conflicts("Conflict check", scheduler3.detect_conflicts())

print("\n" + "=" * 60)
