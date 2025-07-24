import pandas as pd

# # Direct CSV export link for the correct GID
# csv_url = "https://docs.google.com/spreadsheets/d/1Zf9f0z_r7Nx8-y9bY3Z0tWhBK6nuM8bz3Cu5XYNjvwI/export?format=csv&gid=122027575"
# df = pd.read_csv(csv_url)

# # Check the columns first
# print(df.columns)
# print(df)

# df.to_csv("output.csv", index=False)

# df = pd.read_csv("output.csv")

# # If you see the correct column name, extract all IDs (replace 'ID' with actual column name if different)
# ids = df[df.columns[12]].dropna().astype(str).tolist()  # Column M is index 12 (zero-based)
# print(ids)

import pandas as pd
import csv

# Path to your CSV file
input_csv = 'output.csv'  # Change to your actual file name


# All possible stage names
stage_names = [
    'Grand Finals', 'Finals', 'Semifinals', 'Quarterfinals',  "Play-off 1", "Play-off 2", "Playoffs",
    'Round of 16', 'Round of 32', 'Qualifiers'
]

# Read CSV, skip empty lines
df = pd.read_csv(input_csv, header=None, dtype=str, skip_blank_lines=False)

stage_to_ids = {}
current_stage = None

for idx, row in df.iterrows():
    # Check if row indicates a stage change
    for stage in stage_names:
        if stage in str(row.values):
            current_stage = stage
            break
    # If row has enough columns and looks like a map entry, get the ID
    # ID is in column 11 (zero-based index, so it's the 12th column)
    if current_stage and len(row) > 11:
        map_id = str(row[11]).strip()
        if map_id.isdigit():
            if current_stage not in stage_to_ids:
                stage_to_ids[current_stage] = []
            stage_to_ids[current_stage].append(map_id)

# Write CSV for each stage
for stage, ids in stage_to_ids.items():
    output_csv = f"{stage.replace(' ', '_')}_maps.csv"
    with open(output_csv, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Map Link'])
        for map_id in ids:
            writer.writerow([f"https://osu.ppy.sh/beatmaps/{map_id}"])
    print(f"Wrote {output_csv}: {len(ids)} maps")


