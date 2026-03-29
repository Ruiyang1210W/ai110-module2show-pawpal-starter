# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The app is built around three things a user actually needs to do:

1. **Set up their profile and pet info** — The user enters their name, their pet's name and type, and how much free time they have in a day. This is the starting point because the schedule has to fit around the owner's real availability.

2. **Add and manage care tasks** — The user can add tasks like walks, feeding, giving meds, or grooming. Each task has a name, how long it takes, and how important it is. They can also edit or remove tasks as things change.

3. **Generate and read the daily plan** — Once the tasks are in, the user can generate a schedule. The app figures out what fits in the day and puts it in a reasonable order based on priority and time. It also gives a short reason for why the plan looks the way it does.

These three steps follow a simple flow: you describe yourself and your pet, you list what needs to get done, and then the app helps you figure out when to do it.

**b. Design changes**

After reviewing the skeleton, a few things got changed before writing any real logic:

1. **Added `set_pet()` to `Owner`** — The original design left `owner.pet` as a plain attribute with no setter. That meant the only way to assign a pet was to reach directly into the object from outside. Adding `set_pet()` keeps it consistent with how `add_task()` works and makes the intent clearer.

2. **`generate_plan()` now returns `List[CareTask]`** — It used to return `None`, which made the flow confusing. You'd call `generate_plan()`, then separately call `get_plan()` to get anything back. Now `generate_plan()` populates the internal lists *and* returns the result directly. `get_plan()` stays as a simple getter for the cached result if you need it later.

3. **`get_tasks()` now returns `self.tasks` explicitly** — It had `pass` before, which means it would have returned `None`. Since `Scheduler` depends on this method to build the plan, a silent `None` return would have caused hard-to-debug crashes. Fixed it in the stub so there's no ambiguity.

4. **`CareTask.edit()` now covers all four fields** — The original only allowed editing `duration_minutes` and `priority`. Since the UI will let users update tasks, `name` and `category` need to be editable too.

5. **Added priority validation via `__post_init__`** — `priority` is a free string with no guardrails. Added a `VALID_PRIORITIES` constant and a `__post_init__` check that raises a `ValueError` for anything outside `"high"`, `"medium"`, `"low"`. This catches bad input early before it reaches the scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
