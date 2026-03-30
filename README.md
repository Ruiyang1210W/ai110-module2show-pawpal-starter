# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond the basic plan generator, PawPal+ includes several logic improvements built on top of the core scheduler:

**Start time assignment**
Every scheduled task gets a real `HH:MM` start time. The scheduler runs a clock starting at 08:00 and assigns each task a slot based on how long the previous one took. You can see the full day laid out as a timeline, not just a list.

**Sort by time**
`Scheduler.sort_by_time()` returns the scheduled task list ordered by start time using a lambda key that converts `"HH:MM"` strings to integer minutes for comparison. Tasks can be added in any order and still print in chronological sequence.

**Filter by pet or status**
`filter_by_pet(name)` and `filter_by_status(completed)` let you slice the schedule down to just one animal's tasks or just what's still pending. Useful for checking progress mid-day.

**Recurring tasks**
Tasks have a `frequency` field: `"daily"`, `"weekly"`, or `"as-needed"`. When a recurring task is marked done, `CareTask.mark_done()` automatically returns a new instance with the next `due_date` calculated using Python's `timedelta`. The scheduler only includes tasks due today or earlier, so future occurrences stay out of the way until they are needed.

**Conflict detection**
`Scheduler.detect_conflicts()` checks every pair of scheduled tasks for time window overlaps using the interval test `(a_start < b_end) and (b_start < a_end)`. It returns a list of plain-English warning strings rather than raising an exception, so the app can display them without crashing.

---

## Testing PawPal+

To run the tests:

```bash
py -m pytest tests/test_pawpal.py -v
```

There are 37 tests total. They cover the stuff that's easy to get wrong:

- tasks fitting (or not fitting) into the time budget
- priority sorting — high before medium before low, no matter what order you add them
- recurring tasks — daily creates a new one tomorrow, weekly in 7 days, as-needed does nothing
- conflict detection — overlapping time windows get flagged, back-to-back ones don't
- filtering — by pet name or by done/not done
- edge cases — no pets, no tasks, zero minutes available, completing a task twice

**Confidence: 4/5**

The core scheduling logic feels solid. The main thing I'm less sure about is how the app holds up with a lot of pets or tasks — the conflict checker checks every pair, so it'd slow down with a big list. Good enough for a daily pet planner though.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
