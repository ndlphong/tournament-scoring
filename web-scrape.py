import requests
from bs4 import BeautifulSoup
import os
import csv
import re
import sys

# Make script always work in its own directory (even if run from another folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(SCRIPT_DIR)

# Stage names sorted by length (descending) so longer matches come first
stage_names = sorted([
    "Grand Finals", "Finals", "Semifinals", "Quarterfinals",
    "Round of 16", "Round of 32", "Round of 64", "Group stage", "Playoffs", "Play-off 1", "Play-off 2", "Qualifiers"
], key=lambda s: -len(s))

# --- SV REMOVAL RULE FUNCTIONS ---

def remove_last_4_plus_keep_last_2(stage, maps):
    # Remove the third-last and second-last, keep the last (for standard 4K OWC and similar)
    if stage.lower() != "qualifiers" and len(maps) >= 4:
        return maps[:-4] + maps[-2:]
    return maps

def remove_last_3_plus_keep_last(stage, maps):
    # Remove the third-last and second-last, keep the last (for standard 4K OWC and similar)
    if stage.lower() != "qualifiers" and len(maps) >= 3:
        return maps[:-3] + maps[-1:]
    return maps

def remove_last_2_plus_keep_last(stage, maps):
    # Remove the second-last, keep the last (for formats needing 2 SVs removed)
    if stage.lower() != "qualifiers" and len(maps) >= 2:
        return maps[:-2] + maps[-1:]
    return maps

def remove_first_2(stage, maps):
    # Remove the first two maps (for formats needing first 2 SVs removed)
    if stage.lower() != "qualifiers" and len(maps) > 2:
        return maps[2:]
    return maps

def keep_all(stage, maps):
    # Default: don't remove any
    return maps

# --- ASSIGN RULES TO EACH URL ---

urls = [
    # (url, sv_removal_rule)
    ("https://osu.ppy.sh/wiki/en/Tournaments/4DM/2024", remove_last_3_plus_keep_last),
    ("https://osu.ppy.sh/wiki/en/Tournaments/SOFT/5", keep_all), # No SVs, if used
    ("https://osu.ppy.sh/wiki/en/Tournaments/4DM/3", remove_last_3_plus_keep_last),
    ("https://osu.ppy.sh/wiki/en/Tournaments/MWC/2021_4K", remove_last_3_plus_keep_last),
    ("https://osu.ppy.sh/wiki/en/Tournaments/MCNC/4K2022", remove_last_3_plus_keep_last),
    ("https://osu.ppy.sh/wiki/en/Tournaments/OMIC/2022_4K", remove_first_2),
    ("https://osu.ppy.sh/wiki/en/Tournaments/MWC/2024_4K", remove_last_3_plus_keep_last),
    ("https://osu.ppy.sh/wiki/en/Tournaments/JHC/JHC_2024", keep_all),
    ("https://osu.ppy.sh/wiki/en/Tournaments/TMC/4th", keep_all),
    ("https://osu.ppy.sh/wiki/en/Tournaments/SOL/2020", keep_all),
    ("https://osu.ppy.sh/wiki/en/Tournaments/4DM/4", remove_last_3_plus_keep_last), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/SOFT/6", keep_all), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/MWC/2022_4K", remove_last_3_plus_keep_last), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/o%21mLN/3", keep_all), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/MCNC/4k2023", remove_last_4_plus_keep_last_2), # also has playoffs 1 and playoffs 2
    ("https://osu.ppy.sh/wiki/en/Tournaments/GBC/GBC_2023_Autumn", remove_last_3_plus_keep_last), # lets see how this goes
    ("https://osu.ppy.sh/wiki/en/Tournaments/TMC/3rd", keep_all), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/MWC/2023_4K", remove_last_3_plus_keep_last), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/SOL/2023", keep_all), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/GBC/GBC_2024_Spring", keep_all), # lets see how this goes
    ("https://osu.ppy.sh/wiki/en/Tournaments/OMMT/4", remove_last_3_plus_keep_last), 
    ("https://osu.ppy.sh/wiki/en/Tournaments/MCNC/4K2024", remove_last_4_plus_keep_last_2), 
]

# --- SCRAPER FUNCTION ---

def scrape_osu_tournament(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    h1 = soup.find('h1')
    tournament_name = h1.get_text(strip=True) if h1 else 'osu_tournament'

    results = {}

    # Find all relevant headers and store their positions in the HTML tree
    headers = []
    for tag in soup.find_all(['h1','h2','h3','h4','h5']):
        headers.append(tag)

    for i, header in enumerate(headers):
        text = header.get_text(strip=True)
        stage_matched = None
        for stage in stage_names:
            # Use regex to match whole words only
            if re.search(rf'\b{re.escape(stage.lower())}\b', text.lower()):
                stage_matched = stage
                break
        if not stage_matched:
            continue
        if stage_matched not in results:
            results[stage_matched] = {'maps': [], 'matches': []}
        # Collect all tags between this header and the next header
        next_header = headers[i+1] if i+1 < len(headers) else None
        sibling = header.next_sibling
        while sibling and sibling != next_header:
            # If it's a Tag, process it
            if hasattr(sibling, 'find_all'):
                links = sibling.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if href.startswith('/beatmapsets/') or href.startswith('https://osu.ppy.sh/beatmapsets/'):
                        full_url = 'https://osu.ppy.sh' + href if href.startswith('/beatmapsets/') else href
                        results[stage_matched]['maps'].append(full_url)
                    if href.startswith('/community/matches/') or href.startswith('https://osu.ppy.sh/community/matches/'):
                        full_url = 'https://osu.ppy.sh' + href if href.startswith('/community/matches/') else href
                        results[stage_matched]['matches'].append(full_url)
            sibling = sibling.next_sibling

    return tournament_name, results

# --- SAVE TO CSV (USE RULE FROM URL) ---

def save_to_csv(folder, stage, items, sv_rule):
    os.makedirs(folder, exist_ok=True)
    maps = items['maps']
    if sv_rule is not None:
        maps = sv_rule(stage, maps)
    with open(os.path.join(folder, f"{stage}_maps.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Map Link"])
        for url in maps:
            writer.writerow([url])
    with open(os.path.join(folder, f"{stage}_matches.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Match Link"])
        for url in items['matches']:
            writer.writerow([url])

# === MAIN SCRAPE LOOP ===

for url, sv_rule in urls:
    print(f"Scraping: {url}")
    tournament_name, results = scrape_osu_tournament(url)
    folder_name = "".join(c for c in tournament_name if c.isalnum() or c in " _-").rstrip()
    for stage, items in results.items():
        stage_name = "".join(c for c in stage if c.isalnum() or c in " _-").rstrip()
        save_to_csv(folder_name, stage_name, items, sv_rule)
    print(f"Done: {folder_name}")

print("All tournaments scraped!")
