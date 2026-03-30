import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state initialisation
# Only runs the first time — on every subsequent re-run the objects already
# exist in st.session_state, so this block is skipped and data is preserved.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A daily pet care planner that fits tasks around your schedule.")

st.divider()

# ---------------------------------------------------------------------------
# Section 1: Owner profile
# ---------------------------------------------------------------------------
st.subheader("1. Owner Profile")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=5, max_value=480, value=90
    )
    preferences = st.text_input("Preferences (optional)", placeholder="e.g. prefer morning walks")
    submitted = st.form_submit_button("Save profile")

if submitted:
    # Create a fresh Owner, carrying over any existing pets if the owner already existed
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferences=preferences,
    )
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    st.success(f"Profile saved for {owner_name} ({available_minutes} min available).")

if st.session_state.owner:
    owner = st.session_state.owner
    st.caption(
        f"Current profile: **{owner.name}** — {owner.available_minutes} min/day"
        + (f" | Preferences: {owner.preferences}" if owner.preferences else "")
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a pet
# ---------------------------------------------------------------------------
st.subheader("2. Add a Pet")

if not st.session_state.owner:
    st.info("Save your owner profile above before adding pets.")
else:
    with st.form("pet_form"):
        pet_name = st.text_input("Pet name", value="Luna")
        species   = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        age       = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        notes     = st.text_input("Notes (optional)", placeholder="e.g. has a bad hip")
        add_pet   = st.form_submit_button("Add pet")

    if add_pet:
        owner = st.session_state.owner
        # Prevent duplicate pet names
        if owner.get_pet(pet_name):
            st.warning(f"{pet_name} is already in your list.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=age, notes=notes))
            st.success(f"Added {pet_name} the {species}!")

    # Show current pets
    owner = st.session_state.owner
    if owner.pets:
        st.write("**Your pets:**")
        for pet in owner.pets:
            label = f"🐾 {pet.summary()}"
            if pet.notes:
                label += f" — {pet.notes}"
            st.markdown(label)
    else:
        st.info("No pets added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Add a task to a pet
# ---------------------------------------------------------------------------
st.subheader("3. Add a Care Task")

owner = st.session_state.owner
if not owner or not owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        pet_options = [p.name for p in owner.pets]
        selected_pet = st.selectbox("Assign to pet", pet_options)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task name", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
        with col5:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

        add_task = st.form_submit_button("Add task")

    if add_task:
        pet = owner.get_pet(selected_pet)
        try:
            pet.add_task(CareTask(
                name=task_name,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                frequency=frequency,
            ))
            st.success(f"Added '{task_name}' to {selected_pet}'s task list.")
        except ValueError as e:
            st.error(str(e))

    # Show all tasks across all pets
    all_pairs = owner.get_all_tasks()
    if all_pairs:
        st.write("**All current tasks:**")
        rows = [
            {
                "Pet": pet.name,
                "Task": task.name,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Category": task.category,
                "Done": "Yes" if task.completed else "No",
            }
            for pet, task in all_pairs
        ]
        st.table(rows)
    else:
        st.info("No tasks added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate schedule
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

owner = st.session_state.owner
if not owner or not owner.get_all_pending_tasks():
    st.info("Add an owner, at least one pet, and at least one task to generate a schedule.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(owner)
        scheduler.generate_plan()
        st.session_state.scheduler = scheduler

    if st.session_state.scheduler:
        scheduler = st.session_state.scheduler
        scheduled = scheduler.scheduled_tasks
        skipped   = scheduler.skipped_tasks
        total_min = sum(t.duration_minutes for _, t in scheduled)

        st.success(f"Plan ready — {total_min} of {owner.available_minutes} minutes used.")

        if scheduled:
            st.markdown("#### Scheduled tasks")
            for i, (pet, task) in enumerate(scheduled, start=1):
                st.markdown(
                    f"**{i}. {task.name}** for {pet.name} "
                    f"| {task.duration_minutes} min | Priority: `{task.priority}`"
                )

        if skipped:
            st.markdown("#### Skipped (not enough time)")
            for pet, task in skipped:
                st.markdown(
                    f"- ~~{task.name}~~ for {pet.name} "
                    f"| needs {task.duration_minutes} min"
                )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
