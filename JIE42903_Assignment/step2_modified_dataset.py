
import csv
import random

# ==========================================
# 1. GENETIC ALGORITHM PARAMETERS
# ==========================================

GEN = 100
POP = 50
CO_R = 0.8
MUT_R = 0.02
EL_S = 2

random.seed(42)


# ==========================================
# 2. READ MODIFIED CSV DATASET
# ==========================================

def read_csv_to_dict(file_path):

    program_ratings = {}

    with open(file_path, mode="r", newline="") as file:

        reader = csv.reader(file)
        header = next(reader)

        for row in reader:

            program = row[0]
            ratings_list = [float(value) for value in row[1:]]

            program_ratings[program] = ratings_list

    return header, program_ratings


# IMPORTANT: Using modified dataset
file_path = "modified_program_ratings.csv"

header, ratings = read_csv_to_dict(file_path)

all_programs = list(ratings.keys())
all_time_slots = header[1:]

NUM_SLOTS = len(all_time_slots)


# ==========================================
# 3. DATASET VALIDATION
# ==========================================

if not all_programs:
    raise ValueError("No programs found in CSV.")

if any(len(values) != NUM_SLOTS for values in ratings.values()):
    raise ValueError("Invalid number of ratings.")

if POP < 3:
    raise ValueError("Population must be at least 3.")

if EL_S < 1 or EL_S >= POP:
    raise ValueError("Invalid elitism size.")

if GEN < 1:
    raise ValueError("Generation count must be positive.")

if not 0 <= CO_R <= 0.95:
    raise ValueError("Invalid crossover rate.")

if not 0.01 <= MUT_R <= 0.05:
    raise ValueError("Invalid mutation rate.")

if any(
    value < 0.0 or value > 0.6
    for values in ratings.values()
    for value in values
):
    raise ValueError("Ratings must be between 0.0 and 0.6.")

print("=" * 60)
print("TV SCHEDULING - MODIFIED DATASET")
print("=" * 60)

print("Dataset loaded successfully.")
print("Dataset:", file_path)
print("Total programs:", len(all_programs))
print("Total time slots:", NUM_SLOTS)


# ==========================================
# 4. FITNESS FUNCTION
# ==========================================

def fitness_function(schedule):

    total_rating = 0

    for slot_index, program in enumerate(schedule):

        total_rating += ratings[program][slot_index]

    return total_rating


# ==========================================
# 5. INITIALIZE POPULATION
# ==========================================

def initialize_population():

    population = []

    for _ in range(POP):

        schedule = [
            random.choice(all_programs)
            for _ in range(NUM_SLOTS)
        ]

        population.append(schedule)

    return population


# ==========================================
# 6. SELECTION - TOURNAMENT
# ==========================================

def selection(population, tournament_size=3):

    candidates = random.sample(
        population,
        tournament_size
    )

    best_candidate = max(
        candidates,
        key=fitness_function
    )

    return best_candidate.copy()


# ==========================================
# 7. CROSSOVER
# ==========================================

def crossover(parent1, parent2):

    crossover_point = random.randint(
        1,
        NUM_SLOTS - 1
    )

    child1 = (
        parent1[:crossover_point]
        + parent2[crossover_point:]
    )

    child2 = (
        parent2[:crossover_point]
        + parent1[crossover_point:]
    )

    return child1, child2


# ==========================================
# 8. MUTATION
# ==========================================

def mutate(schedule):

    mutation_point = random.randint(
        0,
        NUM_SLOTS - 1
    )

    new_program = random.choice(all_programs)

    schedule[mutation_point] = new_program

    return schedule


# ==========================================
# 9. GENETIC ALGORITHM
# ==========================================

def genetic_algorithm():

    population = initialize_population()

    best_fitness_history = []

    for generation in range(GEN):

        # Sort population by fitness
        population.sort(
            key=fitness_function,
            reverse=True
        )

        # Elitism
        new_population = [
            individual.copy()
            for individual in population[:EL_S]
        ]

        # Generate offspring
        while len(new_population) < POP:

            parent1 = selection(population)
            parent2 = selection(population)

            # Crossover
            if random.random() < CO_R:

                child1, child2 = crossover(
                    parent1,
                    parent2
                )

            else:

                child1 = parent1.copy()
                child2 = parent2.copy()

            # Mutation
            if random.random() < MUT_R:
                child1 = mutate(child1)

            if random.random() < MUT_R:
                child2 = mutate(child2)

            new_population.append(child1)

            if len(new_population) < POP:
                new_population.append(child2)

        population = new_population

        # Record best fitness
        best_fitness = max(
            fitness_function(schedule)
            for schedule in population
        )

        best_fitness_history.append(best_fitness)

        if (generation + 1) % 10 == 0:

            print(
                f"Generation {generation + 1}: "
                f"Best Fitness = {best_fitness:.2f}"
            )

    best_schedule = max(
        population,
        key=fitness_function
    )

    return best_schedule, best_fitness_history


# ==========================================
# 10. RUN GENETIC ALGORITHM
# ==========================================

print("\nStarting Genetic Algorithm...")

best_schedule, fitness_history = genetic_algorithm()


# ==========================================
# 11. DISPLAY FINAL SCHEDULE
# ==========================================

print("\n" + "=" * 65)
print("FINAL TV PROGRAM SCHEDULE - MODIFIED DATA")
print("=" * 65)

for index, program in enumerate(best_schedule):

    print(
        f"{all_time_slots[index]:12} | "
        f"{program:20} | "
        f"Rating: {ratings[program][index]:.2f}"
    )


# ==========================================
# 12. CALCULATE FINAL FITNESS
# ==========================================

final_fitness = fitness_function(best_schedule)


# ==========================================
# 13. THEORETICAL OPTIMUM BENCHMARK
# ==========================================

optimal_schedule = []

for slot_index in range(NUM_SLOTS):

    best_program = max(
        all_programs,
        key=lambda program: ratings[program][slot_index]
    )

    optimal_schedule.append(best_program)


theoretical_maximum = fitness_function(optimal_schedule)

fitness_gap = theoretical_maximum - final_fitness

if theoretical_maximum > 0:

    efficiency = (
        final_fitness / theoretical_maximum
    ) * 100

else:

    efficiency = 0


# ==========================================
# 14. DISPLAY PERFORMANCE RESULTS
# ==========================================

print("\n" + "=" * 65)
print("MODIFIED DATASET - PERFORMANCE RESULTS")
print("=" * 65)

print("Dataset:", file_path)
print("Generations:", GEN)
print("Population Size:", POP)
print("Crossover Rate:", CO_R)
print("Mutation Rate:", MUT_R)
print("Elitism Size:", EL_S)

print("-" * 65)

print(f"GA Fitness:          {final_fitness:.2f}")
print(f"Theoretical Optimum: {theoretical_maximum:.2f}")
print(f"Fitness Gap:         {fitness_gap:.2f}")
print(f"GA Efficiency:       {efficiency:.2f}%")

print("\nGenetic Algorithm completed successfully!")
