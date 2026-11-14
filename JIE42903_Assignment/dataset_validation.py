
import csv

# ==========================================
# STEP 1: LOAD PROGRAM RATINGS
# ==========================================

def read_csv_to_dict(file_path):
    program_ratings = {}

    with open(file_path, mode="r", newline="") as file:
        reader = csv.reader(file)

        header = next(reader)

        for row in reader:
            program = row[0]
            ratings = [float(value) for value in row[1:]]

            program_ratings[program] = ratings

    return header, program_ratings


# ==========================================
# STEP 2: READ DATASET
# ==========================================

file_path = "program_ratings.csv"

header, ratings = read_csv_to_dict(file_path)

# ==========================================
# STEP 3: VALIDATE DATASET
# ==========================================

all_programs = list(ratings.keys())
all_time_slots = header[1:]

print("=" * 50)
print("TV SCHEDULING - DATASET VALIDATION")
print("=" * 50)

print(f"Total programs: {len(all_programs)}")
print(f"Total time slots: {len(all_time_slots)}")

print("\nProgram details:")

for program, values in ratings.items():
    print(f"{program:20} | Ratings: {len(values)}")

# Check dataset consistency
valid = all(
    len(values) == len(all_time_slots)
    for values in ratings.values()
)

if valid:
    print("\nSUCCESS: All programs have 18 ratings.")
else:
    print("\nERROR: Some programs have missing ratings.")

print("\nTime slots:")
print(all_time_slots)

print("\nDataset validation completed.")
