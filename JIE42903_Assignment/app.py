
import csv
import random
import streamlit as st
import pandas as pd
from pathlib import Path

# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="TV Scheduling Optimizer",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

GEN = 100
POP = 50
EL_S = 2

# =========================================================
# 2. PROFESSIONAL DARK DASHBOARD THEME
# =========================================================

st.markdown("""
<style>
:root {
    --bg: #0b1222;
    --panel: #17243a;
    --border: #2a3c59;
    --muted: #98a9c2;
    --text: #eef4ff;
    --blue: #6685ff;
    --purple: #9b75ee;
    --green: #43d6a0;
}

.stApp {
    background: #0b1222;
    color: #eef4ff;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1600px;
    padding: 1.5rem 2rem 2rem;
}

[data-testid="stSidebar"] {
    background: #111a2c;
    border-right: 1px solid #283957;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #c2cde0;
}

h1, h2, h3, h4 {
    color: #eef4ff !important;
}

p, label {
    color: #c0cbe0;
}

hr {
    border-color: #283957;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1a2944, #17233a);
    border: 1px solid #2b3e60;
    border-radius: 13px;
    padding: 17px 19px;
    min-height: 110px;
}

[data-testid="stMetricLabel"] {
    color: #aebbd1 !important;
}

[data-testid="stMetricValue"] {
    color: #f4f7ff !important;
    font-weight: 750;
}

[data-testid="stMetricDelta"] {
    color: #58d6a5 !important;
}

.stButton > button {
    border-radius: 8px;
    border: 1px solid #4768d8;
    background: #526ff0;
    color: white;
    font-weight: 650;
    min-height: 2.55rem;
}

.stButton > button:hover {
    background: #405fdc;
    color: white;
    border-color: #7894ff;
}

.stDownloadButton > button {
    background: #1d2c49;
    color: white;
    border: 1px solid #354d75;
    border-radius: 8px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #2a3c5a;
    border-radius: 10px;
    overflow: hidden;
}

[data-testid="stExpander"] {
    border: 1px solid #2a3c5a;
    border-radius: 10px;
    background: #141f33;
}

div[data-baseweb="select"] > div {
    background: #17243a;
    border-color: #344867;
}

.stSlider {
    padding-top: 5px;
}

div[data-testid="stTabs"] button {
    color: #b8c6dc;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #8da5ff !important;
    border-bottom-color: #6684ff !important;
}

.eyebrow {
    color: #7894ff;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.7px;
}

.hero-title {
    font-size: 29px;
    font-weight: 760;
    color: #f4f7ff;
    margin-top: 5px;
}

.hero-sub {
    color: #9eacc4;
    font-size: 13px;
    margin-top: 5px;
}

.panel-title {
    color: #eff4ff;
    font-weight: 700;
    font-size: 17px;
}

.panel-sub {
    color: #94a5bf;
    font-size: 12px;
}

.pill {
    display: inline-block;
    border-radius: 20px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 700;
    color: #7ce3ba;
    background: #173b38;
    border: 1px solid #27685d;
}

footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. DATA LOADING
# =========================================================

@st.cache_data
def load_dataset(path):

    data = {}

    with open(
        path,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.reader(file)
        header = next(reader)

        for row in reader:

            if not row:
                continue

            name = row[0].strip()

            if name in data:
                raise ValueError(
                    f"Duplicate program: {name}"
                )

            data[name] = [
                float(value) for value in row[1:]
            ]

    return header, data


try:

    DATA_DIR = Path(__file__).resolve().parent

    original_header, original_ratings = load_dataset(
        DATA_DIR / "program_ratings.csv"
    )

    header, ratings = load_dataset(
        DATA_DIR / "modified_program_ratings.csv"
    )

except FileNotFoundError as error:

    st.error(
        f"Missing CSV file: {error.filename}. "
        "Keep both CSV files in the same folder as app.py."
    )
    st.stop()

except (ValueError, StopIteration) as error:

    st.error(f"Dataset loading error: {error}")
    st.stop()


programs = list(ratings.keys())
time_slots = header[1:]
num_slots = len(time_slots)


# =========================================================
# 4. DATASET VALIDATION
# =========================================================

if not programs or not time_slots:
    st.error("Dataset contains no programs or time slots.")
    st.stop()

if num_slots < 2:
    st.error("At least two time slots are required.")
    st.stop()

if original_header != header:
    st.error("Original and modified CSV headers do not match.")
    st.stop()

if list(original_ratings.keys()) != programs:
    st.error("Program names or ordering do not match.")
    st.stop()

if any(len(v) != num_slots for v in ratings.values()):
    st.error("Some programs have missing ratings.")
    st.stop()

if any(
    not 0.0 <= value <= 0.6
    for values in ratings.values()
    for value in values
):
    st.error("Ratings must be between 0.0 and 0.6.")
    st.stop()

total_changes = sum(
    old != new
    for name in programs
    for old, new in zip(
        original_ratings[name],
        ratings[name]
    )
)


# =========================================================
# 5. FITNESS FUNCTION
# =========================================================

def fitness_function(schedule):

    return sum(
        ratings[program][i]
        for i, program in enumerate(schedule)
    )


# =========================================================
# 6. INITIALIZE POPULATION
# =========================================================

def initialize_population():

    return [
        [
            random.choice(programs)
            for _ in range(num_slots)
        ]
        for _ in range(POP)
    ]


# =========================================================
# 7. TOURNAMENT SELECTION
# =========================================================

def selection(population, tournament_size=3):

    candidates = random.sample(
        population,
        tournament_size
    )

    return max(
        candidates,
        key=fitness_function
    ).copy()


# =========================================================
# 8. CROSSOVER
# =========================================================

def crossover(parent1, parent2):

    point = random.randint(1, num_slots - 1)

    child1 = (
        parent1[:point] + parent2[point:]
    )

    child2 = (
        parent2[:point] + parent1[point:]
    )

    return child1, child2


# =========================================================
# 9. MUTATION
# =========================================================

def mutate(schedule):

    point = random.randint(0, num_slots - 1)

    schedule[point] = random.choice(programs)

    return schedule


# =========================================================
# 10. GENETIC ALGORITHM
# =========================================================

def genetic_algorithm(
    crossover_rate,
    mutation_rate,
    seed=42
):

    random.seed(seed)

    population = initialize_population()

    history = []

    for generation in range(GEN):

        population.sort(
            key=fitness_function,
            reverse=True
        )

        new_population = [
            individual.copy()
            for individual in population[:EL_S]
        ]

        while len(new_population) < POP:

            parent1 = selection(population)
            parent2 = selection(population)

            if random.random() < crossover_rate:

                child1, child2 = crossover(
                    parent1,
                    parent2
                )

            else:

                child1 = parent1.copy()
                child2 = parent2.copy()

            if random.random() < mutation_rate:
                child1 = mutate(child1)

            if random.random() < mutation_rate:
                child2 = mutate(child2)

            new_population.append(child1)

            if len(new_population) < POP:
                new_population.append(child2)

        population = new_population

        best_fitness = max(
            fitness_function(individual)
            for individual in population
        )

        history.append(best_fitness)

    best_schedule = max(
        population,
        key=fitness_function
    )

    return best_schedule, history


# =========================================================
# 11. THEORETICAL OPTIMUM
# =========================================================

optimal_schedule = [

    max(
        programs,
        key=lambda program: ratings[program][i]
    )

    for i in range(num_slots)
]

theoretical_maximum = fitness_function(
    optimal_schedule
)


# =========================================================
# 12. PERFORMANCE METRICS
# =========================================================

def result_metrics(schedule):

    score = fitness_function(schedule)

    gap = theoretical_maximum - score

    efficiency = (
        score / theoretical_maximum * 100
        if theoretical_maximum > 0
        else 0
    )

    return {
        "Fitness": round(score, 2),
        "Theoretical Optimum": round(
            theoretical_maximum, 2
        ),
        "Fitness Gap": round(gap, 2),
        "Efficiency": round(efficiency, 2)
    }


# =========================================================
# 13. SCHEDULE DATAFRAME
# =========================================================

def schedule_frame(schedule):

    return pd.DataFrame([

        {
            "Time Slot": time_slots[i],
            "Program": program,
            "Audience Rating": ratings[program][i]
        }

        for i, program in enumerate(schedule)

    ])


# =========================================================
# 14. RATING SUMMARY
# =========================================================

def rating_summary():

    return pd.DataFrame([

        {
            "Program": name,
            "Average Rating": sum(values) / len(values),
            "Peak Rating": max(values),
            "Lowest Rating": min(values)
        }

        for name, values in ratings.items()

    ]).sort_values(
        "Average Rating",
        ascending=False
    )


# =========================================================
# 15. SESSION STATE
# =========================================================

if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

if "experiment_results" not in st.session_state:
    st.session_state.experiment_results = None


# =========================================================
# 16. SIDEBAR
# =========================================================

with st.sidebar:

    # IMPORTANT: Use st.html for HTML fragments.
    st.html("""
    <div style="padding:10px 5px 24px 5px;">
        <div style="
            font-size:22px;
            font-weight:800;
            color:#f2f5ff;
        ">
            ◈ TV Optimizer
        </div>

        <div style="
            font-size:10px;
            letter-spacing:1.8px;
            color:#819cff;
            margin-top:5px;
        ">
            INTELLIGENT SCHEDULING
        </div>
    </div>

    <div style="
        font-size:10px;
        font-weight:800;
        letter-spacing:1.7px;
        color:#7894ff;
    ">
        MAIN MENU
    </div>
    """)

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Schedule Generator",
            "Experiment Lab",
            "Analytics",
            "Dataset Explorer"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.html("""
    <div style="
        font-size:10px;
        font-weight:800;
        letter-spacing:1.5px;
        color:#7894ff;
    ">
        WORKSPACE
    </div>
    """)

    st.caption("Evolutionary Computing")
    st.caption("JIE42903 Assignment")

    st.divider()

    st.html("""
    <span style="
        display:inline-block;
        padding:6px 10px;
        border-radius:20px;
        color:#7ce3ba;
        background:#173b38;
        border:1px solid #27685d;
        font-size:10px;
        font-weight:700;
    ">
        ● DATASET CONNECTED
    </span>
    """)

    st.write("")
    st.caption(f"{len(programs)} programs · {num_slots} time slots")
    st.caption(f"{total_changes} modified ratings")


# =========================================================
# 17. TOP HEADER
# =========================================================

left, right = st.columns([2.3, 1])

with left:

    st.markdown(
        f"""
        <div class="eyebrow">
            TV SCHEDULING / {page.upper()}
        </div>
        <div class="hero-title">
            {page}
        </div>
        <div class="hero-sub">
            Genetic Algorithm-based television program scheduling
        </div>
        """,
        unsafe_allow_html=True
    )

with right:

    search_text = st.text_input(
        "Search",
        placeholder="Search program...",
        label_visibility="collapsed"
    )

    if search_text:

        matches = [
            p for p in programs
            if search_text.lower() in p.lower()
        ]

        if matches:
            st.caption("Matches: " + ", ".join(matches))
        else:
            st.caption("No matching program found.")

st.divider()


# =========================================================
# 18. DASHBOARD
# =========================================================

if page == "Dashboard":

    heading_left, heading_right = st.columns([3, 1])

    with heading_left:
        st.subheader("Performance overview")

    with heading_right:
        st.html("""
        <div style="text-align:right;padding-top:10px;">
            <span class="pill">● SYSTEM ONLINE</span>
        </div>
        """)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total programs",
        len(programs),
        "Loaded from dataset"
    )

    c2.metric(
        "Broadcast time slots",
        num_slots,
        f"{time_slots[0]} – {time_slots[-1]}"
    )

    c3.metric(
        "Rating modifications",
        total_changes,
        "Original vs modified"
    )

    c4.metric(
        "GA generations",
        GEN,
        f"Population {POP}"
    )

    st.write("")

    chart_col, insight_col = st.columns([1.8, 1])

    with chart_col:

        st.markdown("#### Audience rating by program")

        st.caption(
            "Average audience rating across all time slots"
        )

        summary = rating_summary().set_index(
            "Program"
        )[["Average Rating"]]

        st.bar_chart(
            summary,
            color="#6685ff",
            height=300
        )

    with insight_col:

        st.markdown("#### Dataset snapshot")

        st.caption("Current modified ratings dataset")

        average_rating = (
            sum(sum(v) for v in ratings.values())
            / (len(programs) * num_slots)
        )

        st.metric(
            "Average rating",
            f"{average_rating:.3f}"
        )

        st.metric(
            "Highest individual rating",
            f"{max(max(v) for v in ratings.values()):.2f}"
        )

        st.metric(
            "Lowest individual rating",
            f"{min(min(v) for v in ratings.values()):.2f}"
        )

    st.divider()

    bottom_left, bottom_right = st.columns([1.2, 1])

    with bottom_left:

        st.markdown("#### Average rating by time slot")

        slot_avg = pd.DataFrame({

            "Average Rating": [

                sum(
                    ratings[p][i]
                    for p in programs
                ) / len(programs)

                for i in range(num_slots)
            ]

        }, index=time_slots)

        st.line_chart(
            slot_avg,
            color="#9b75ee",
            height=250
        )

    with bottom_right:

        st.markdown("#### Optimization status")

        if st.session_state.schedule_result is None:

            st.info(
                "No schedule generated yet. "
                "Open Schedule Generator to begin."
            )

        else:

            metrics = st.session_state.schedule_result[
                "metrics"
            ]

            st.metric(
                "Best fitness",
                f"{metrics['Fitness']:.2f}"
            )

            st.metric(
                "GA efficiency",
                f"{metrics['Efficiency']:.2f}%"
            )

            st.metric(
                "Fitness gap",
                f"{metrics['Fitness Gap']:.2f}"
            )

        if st.session_state.experiment_results is not None:
            st.success("Experimental results available.")

    st.divider()

    st.markdown("#### Top-rated programs")

    top = rating_summary().head(5).copy()

    top["Average Rating"] = top[
        "Average Rating"
    ].round(3)

    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 19. SCHEDULE GENERATOR
# =========================================================

elif page == "Schedule Generator":

    st.markdown(
        '<div class="eyebrow">OPTIMIZATION ENGINE</div>',
        unsafe_allow_html=True
    )

    st.header("Generate a TV schedule")

    st.caption(
        "Configure genetic algorithm parameters "
        "to generate an optimized broadcast schedule."
    )

    p1, p2 = st.columns(2)

    with p1:

        crossover_rate = st.slider(
            "Crossover rate",
            0.0,
            0.95,
            0.80,
            0.05
        )

    with p2:

        mutation_rate = st.slider(
            "Mutation rate",
            0.01,
            0.05,
            0.02,
            0.01
        )

    a, b, c = st.columns(3)

    a.metric("Population size", POP)
    b.metric("Generations", GEN)
    c.metric("Elitism size", EL_S)

    if st.button(
        "Generate optimized schedule",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("Running Genetic Algorithm..."):

            schedule, history = genetic_algorithm(
                crossover_rate,
                mutation_rate,
                seed=42
            )

            st.session_state.schedule_result = {

                "schedule": schedule,
                "history": history,
                "metrics": result_metrics(schedule),
                "crossover_rate": crossover_rate,
                "mutation_rate": mutation_rate
            }

        st.success("Optimization completed successfully.")

    if st.session_state.schedule_result is not None:

        result = st.session_state.schedule_result
        metrics = result["metrics"]

        st.divider()

        st.subheader("Optimization results")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("GA fitness", f"{metrics['Fitness']:.2f}")

        c2.metric(
            "Theoretical optimum",
            f"{metrics['Theoretical Optimum']:.2f}"
        )

        c3.metric(
            "Efficiency",
            f"{metrics['Efficiency']:.2f}%"
        )

        c4.metric(
            "Fitness gap",
            f"{metrics['Fitness Gap']:.2f}"
        )

        st.subheader("Generated broadcast schedule")

        frame = schedule_frame(result["schedule"])

        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Audience Rating":
                    st.column_config.ProgressColumn(
                        "Audience Rating",
                        min_value=0.0,
                        max_value=0.6,
                        format="%.2f"
                    )
            }
        )

        st.download_button(
            "Download schedule CSV",
            frame.to_csv(index=False).encode("utf-8"),
            "generated_tv_schedule.csv",
            "text/csv"
        )

        st.subheader("Fitness convergence")

        history_df = pd.DataFrame(
            {"Best Fitness": result["history"]},
            index=range(1, GEN + 1)
        )

        history_df.index.name = "Generation"

        st.line_chart(
            history_df,
            color="#6685ff",
            height=300
        )


# =========================================================
# 20. EXPERIMENT LAB
# =========================================================

elif page == "Experiment Lab":

    st.markdown(
        '<div class="eyebrow">CONTROLLED EXPERIMENTS</div>',
        unsafe_allow_html=True
    )

    st.header("Experiment laboratory")

    st.caption(
        "Compare three crossover and mutation configurations."
    )

    defaults = [
        (0.80, 0.02),
        (0.70, 0.03),
        (0.90, 0.05)
    ]

    params = []

    for i, (default_co, default_mut) in enumerate(defaults):

        with st.expander(
            f"Trial {i + 1} configuration",
            expanded=True
        ):

            x, y = st.columns(2)

            with x:

                co = st.slider(
                    f"Trial {i + 1} crossover rate",
                    0.0,
                    0.95,
                    default_co,
                    0.05,
                    key=f"exp_co_{i}"
                )

            with y:

                mu = st.slider(
                    f"Trial {i + 1} mutation rate",
                    0.01,
                    0.05,
                    default_mut,
                    0.01,
                    key=f"exp_mu_{i}"
                )

            params.append((co, mu))

    if st.button(
        "Run all three trials",
        type="primary",
        use_container_width=True
    ):

        rows = []
        details = []

        progress = st.progress(0)
        status = st.empty()

        for i, (co, mu) in enumerate(params):

            status.write(f"Running Trial {i + 1} of 3...")

            schedule, history = genetic_algorithm(
                co,
                mu,
                seed=42 + i
            )

            metrics = result_metrics(schedule)

            rows.append({

                "Trial": f"Trial {i + 1}",
                "Crossover Rate": co,
                "Mutation Rate": mu,
                "Fitness": metrics["Fitness"],
                "Theoretical Optimum": (
                    metrics["Theoretical Optimum"]
                ),
                "Fitness Gap": metrics["Fitness Gap"],
                "Efficiency (%)": metrics["Efficiency"]

            })

            details.append({

                "schedule": schedule,
                "history": history,
                "metrics": metrics

            })

            progress.progress((i + 1) / 3)

        st.session_state.experiment_results = {

            "comparison": pd.DataFrame(rows),
            "details": details

        }

        status.success("All three experiments completed.")

    if st.session_state.experiment_results is not None:

        stored = st.session_state.experiment_results

        comparison = stored["comparison"]
        details = stored["details"]

        st.divider()

        st.subheader("Trial comparison")

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("#### Fitness by trial")

            st.bar_chart(
                comparison.set_index("Trial")[["Fitness"]],
                color="#6685ff"
            )

        with c2:

            st.markdown("#### Efficiency by trial")

            st.bar_chart(
                comparison.set_index("Trial")[["Efficiency (%)"]],
                color="#43d6a0"
            )

        best_index = int(
            comparison["Fitness"].idxmax()
        )

        best = comparison.iloc[best_index]

        st.success(
            f"Best observed configuration: {best['Trial']} "
            f"with fitness {best['Fitness']:.2f}."
        )

        st.caption(
            "This is the best observed result among the "
            "three configurations tested."
        )

        for i, detail in enumerate(details):

            with st.expander(
                f"Trial {i + 1} schedule and convergence"
            ):

                st.metric(
                    "Fitness",
                    f"{detail['metrics']['Fitness']:.2f}"
                )

                st.dataframe(
                    schedule_frame(detail["schedule"]),
                    use_container_width=True,
                    hide_index=True
                )

                st.line_chart(
                    pd.DataFrame(
                        {"Best Fitness": detail["history"]},
                        index=range(1, GEN + 1)
                    ),
                    color="#6685ff"
                )

        st.download_button(
            "Download experiment comparison",
            comparison.to_csv(index=False).encode("utf-8"),
            "experimental_results.csv",
            "text/csv"
        )


# =========================================================
# 21. ANALYTICS
# =========================================================

elif page == "Analytics":

    st.markdown(
        '<div class="eyebrow">DATA INSIGHTS</div>',
        unsafe_allow_html=True
    )

    st.header("Analytics")

    st.caption(
        "Explore audience rating patterns "
        "and optimization performance."
    )

    left, right = st.columns(2)

    with left:

        st.markdown("#### Average rating by program")

        st.bar_chart(
            rating_summary().set_index("Program")[
                ["Average Rating"]
            ],
            color="#6685ff"
        )

    with right:

        st.markdown("#### Rating by time slot")

        slot_df = pd.DataFrame({

            "Average Rating": [

                sum(
                    ratings[p][i]
                    for p in programs
                ) / len(programs)

                for i in range(num_slots)

            ]

        }, index=time_slots)

        st.line_chart(
            slot_df,
            color="#9b75ee"
        )

    st.divider()

    if st.session_state.schedule_result is not None:

        result = st.session_state.schedule_result
        metrics = result["metrics"]

        a, b, c = st.columns(3)

        a.metric(
            "Latest GA fitness",
            f"{metrics['Fitness']:.2f}"
        )

        b.metric(
            "Efficiency",
            f"{metrics['Efficiency']:.2f}%"
        )

        c.metric(
            "Fitness gap",
            f"{metrics['Fitness Gap']:.2f}"
        )

        st.subheader("Fitness convergence")

        st.line_chart(
            pd.DataFrame(
                {"Best Fitness": result["history"]},
                index=range(1, GEN + 1)
            ),
            color="#6685ff"
        )

    else:

        st.info(
            "Generate a schedule to populate optimization analytics."
        )

    if st.session_state.experiment_results is not None:

        st.subheader("Experimental results")

        st.dataframe(
            st.session_state.experiment_results["comparison"],
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# 22. DATASET EXPLORER
# =========================================================

elif page == "Dataset Explorer":

    st.markdown(
        '<div class="eyebrow">DATA MANAGEMENT</div>',
        unsafe_allow_html=True
    )

    st.header("Dataset explorer")

    st.caption(
        "Inspect the original and modified audience-rating datasets."
    )

    a, b, c = st.columns(3)

    a.metric("Programs", len(programs))
    b.metric("Time slots", num_slots)
    c.metric("Changed ratings", total_changes)

    choice = st.radio(
        "Dataset view",
        ["Modified dataset", "Original dataset"],
        horizontal=True
    )

    selected = (
        ratings
        if choice == "Modified dataset"
        else original_ratings
    )

    table_rows = []

    for name, values in selected.items():

        row = {"Program": name}

        row.update({

            time_slots[i]: values[i]

            for i in range(num_slots)

        })

        table_rows.append(row)

    dataset_df = pd.DataFrame(table_rows)

    st.dataframe(
        dataset_df,
        use_container_width=True,
        hide_index=True
    )

    filename = (
        "modified_program_ratings.csv"
        if choice == "Modified dataset"
        else "program_ratings.csv"
    )

    st.download_button(
        "Download selected dataset",
        dataset_df.to_csv(index=False).encode("utf-8"),
        filename,
        "text/csv"
    )

    st.divider()

    st.subheader("Rating change audit")

    changes = []

    for name in programs:

        for i, slot in enumerate(time_slots):

            old = original_ratings[name][i]
            new = ratings[name][i]

            if old != new:

                changes.append({

                    "Program": name,
                    "Time Slot": slot,
                    "Original Rating": old,
                    "Modified Rating": new,
                    "Difference": round(new - old, 2)

                })

    if changes:

        changes_df = pd.DataFrame(changes)

        st.metric(
            "Total changes detected",
            len(changes_df)
        )

        st.dataframe(
            changes_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download rating change audit",
            changes_df.to_csv(index=False).encode("utf-8"),
            "rating_changes_comparison.csv",
            "text/csv"
        )

    else:

        st.info("No rating differences detected.")


# =========================================================
# 23. FOOTER
# =========================================================

st.divider()

st.html("""
<div style="
    text-align:center;
    padding:12px 0;
    color:#8192ad;
    font-size:11px;
">
    <span style="
        color:#9bb0ff;
        font-weight:800;
        letter-spacing:1px;
    ">
        TV SCHEDULING OPTIMIZER
    </span>
    &nbsp; · &nbsp;
    JIE42903 Evolutionary Computing
    &nbsp; · &nbsp;
    Genetic Algorithm Scheduling System
</div>
""")
