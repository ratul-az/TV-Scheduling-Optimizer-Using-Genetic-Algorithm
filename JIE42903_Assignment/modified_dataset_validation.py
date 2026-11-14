
import csv

# ==========================================
# 1. VALIDATE MODIFIED CSV DATASET
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
# 2. LOAD ORIGINAL AND MODIFIED DATASETS
# ==========================================

original_header, original_ratings = read_csv_to_dict(
    "program_ratings.csv"
)

modified_header, modified_ratings = read_csv_to_dict(
    "modified_program_ratings.csv"
)


# ==========================================
# 3. VALIDATION
# ==========================================

print("=" * 55)
print("MODIFIED DATASET VALIDATION")
print("=" * 55)

print("Total programs:", len(modified_ratings))
print("Total time slots:", len(modified_header) - 1)

assert original_header == modified_header, "CSV headers do not match."

assert original_ratings.keys() == modified_ratings.keys(), (
    "Program names do not match."
)

for program, values in modified_ratings.items():

    assert len(values) == 18, (
        f"{program} does not have 18 ratings."
    )

    assert all(0.0 <= value <= 0.6 for value in values), (
        f"Invalid rating found in {program}."
    )


# ==========================================
# 4. COMPARE ORIGINAL AND MODIFIED RATINGS
# ==========================================

total_changes = 0

for program in original_ratings:

    for old, new in zip(
        original_ratings[program],
        modified_ratings[program]
    ):

        if old != new:
            total_changes += 1


# ==========================================
# 5. DISPLAY RESULTS
# ==========================================

print("\nProgram details:")

for program, values in modified_ratings.items():

    print(f"{program:20} | Ratings: {len(values)}")

print("\nTotal rating changes:", total_changes)

print(
    "Minimum rating:",
    min(min(values) for values in modified_ratings.values())
)

print(
    "Maximum rating:",
    max(max(values) for values in modified_ratings.values())
)

print("\nSUCCESS: Modified dataset validated successfully!")
