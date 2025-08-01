import pandas as pd
from bs4 import BeautifulSoup
import re  # Import the re module for regular expressions

# Define the file path
file_path = r"C:\Users\zakaa\Downloads\Bet with bet365 – Live Online Betting Sportsbook – Latest Bets and Odds.html"

# Function to clean text (remove BB and numbers before "Over")
def clean_text(text):
    text = text.replace("BB", "")  # Remove 'BB'
    text = text.replace("Over", " Over").replace("Under", " Under")  # Add space before "Over" and "Under"
    # Remove all numbers before " Over"
    parts = text.split(" Over", 1)
    if len(parts) > 1:
        parts[0] = re.sub(r'\d+', '', parts[0])  # Remove numbers
        text = " Over".join(parts)
    return text.strip()

# Function to split text into lines for better formatting
def split_text(input_text):
    formatted_text = input_text.replace(" Over", "\nOver").replace(" Under", "\nUnder")
    formatted_text = '\n'.join(line.rstrip() for line in formatted_text.split('\n'))
    return f"\n{formatted_text}\n"

# Function to process a single section
def process_section(soup, start_phrase, end_phrase):
    section_start = soup.find(string=start_phrase)
    section_end = soup.find(string=end_phrase)

    if not (section_start and section_end):
        return None

    # Extract section content
    section_content = []
    for sibling in section_start.find_all_next(string=True):
        if sibling == section_end:
            break
        section_content.append(sibling.strip())

    full_section_text = clean_text(" ".join(section_content).strip())

    # Extract names
    section_div = section_start.find_parent()
    names = []
    if section_div:
        name_divs = section_div.find_all('div', class_="srb-ParticipantLabelWithTeam_Name")
        names = [div.get_text(strip=True) for div in name_divs]

    # Ensure only one space between names
    names_text = re.sub(r'\s+', ' ', " ".join(names))

    # Format the text
    formatted_text = split_text(full_section_text)

    # Parse the formatted text
    lines = formatted_text.splitlines()
    if len(lines) < 4:
        return None  # Not enough lines to process

    player_names = lines[1].split("   ")  # First line of names, separated by spaces
    over_odds = lines[2].replace("Over", "").strip().split()
    under_odds = lines[3].replace("Under", "").strip().split()

    # Combine player names with their odds
    data = []
    for i, name in enumerate(player_names):
        over_index = i * 2
        under_index = i * 2

        if over_index + 1 < len(over_odds) and under_index + 1 < len(under_odds):
            data.append({
                "Player": name,
                "Over": f"{over_odds[over_index]} {over_odds[over_index + 1]}",
                "Under": f"{under_odds[under_index]} {under_odds[under_index + 1]}"
            })

    return pd.DataFrame(data)

# Main script
try:
    with open(file_path, 'r', encoding='utf-8') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')

        # Define sections
        sections = [
            ("Player Shots On Target Over/Under", "Player Shots Over/Under"),
            ("Player Shots Over/Under", "Player Fouls Committed"),
            ("Player Fouls Committed", "Player Tackles"),
            ("Player Tackles", "Player Passes"),
        ]

        # Process each section
        dataframes = {}
        for start_phrase, end_phrase in sections:
            df = process_section(soup, start_phrase, end_phrase)
            if df is not None:
                dataframes[start_phrase] = df

        # Output the dataframes
        for section_name, df in dataframes.items():
            print(f"{section_name}:")
            print(df)
            print("\n" + "=" * 50 + "\n")

except FileNotFoundError:
    print(f"Error: The file at {file_path} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Define a mapping of old names to new names
rename_mapping = {
    "Player Shots On Target Over/Under": "Player_Shots_On_Target",
    "Player Shots Over/Under": "Player_Total_Shots",
    "Player Fouls Committed": "Player_Fouls_Committed",
    "Player Tackles": "Player_Tackles"
}

# Create a new dictionary with renamed keys
renamed_dataframes = {rename_mapping.get(old_name, old_name): df for old_name, df in dataframes.items()}

# Replace the old dictionary with the renamed one
dataframes = renamed_dataframes

# Print the dataframe for "Player Shots On Target Over/Under"
#section_key = "Player Shots On Target Over/Under"

#if section_key in dataframes:
    #print(f"\nDataFrame for '{section_key}':\n")
    #print(tabulate(dataframes[section_key], headers='keys', tablefmt='pretty'))
#else:
    #print(f"Section '{section_key}' not found in the extracted dataframes.")

# Print the renamed DataFrame names
print("Renamed DataFrame Names:")
for section_name in dataframes.keys():
    print(f"- {section_name}")