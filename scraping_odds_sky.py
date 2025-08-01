import pandas as pd
import re
from bs4 import BeautifulSoup
from tabulate import tabulate

# Define the input file path
input_file_path = r"C:\Users\zakaa\Downloads\Manchester City v Everton Betting & Odds » Sky Bet.html"  # Input HTML file path

# Define the start and end phrases for each section
sections = [
    ("Home Player Shots On Target", "Away Player Shots On Target"),
    ("Away Player Shots On Target", "Home Player Fouls Committed"),
    ("Home Player Fouls Committed", "Away Player Fouls Committed"),
    ("Away Player Fouls Committed", "Home Player Total Shots"),
    ("Home Player Total Shots", "Away Player Total Shots"),
    ("Away Player Total Shots", "Home Player Tackles"),
    ("Home Player Tackles", "Away Player Tackles"),
    ("Away Player Tackles", "Home Player Offsides"),
]

# Regular expressions to match unwanted text with flexible spacing
unwanted_text_patterns = [
    r"icon-arrow-up\s*-\s*Opta\s*collect\s*data\s*for\s*all\s*competitions\s*that\s*Sky\s*Bet\s*offer\s*stats\s*markets\s*on\.\s*Sky\s*Bet\s*will\s*always\s*reference\s*Opta\s*for\s*resulting\.",
    r"Show\s*Less\s*icon-arrow-up\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star",
    r"Full\s*market\s*rules\s*available\s*via\s*the\s*Help\s*and\s*Support\s*page\.",
    r"Home\s*Player\s*Fouls\s*Won\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star\s*Away\s*Player\s*Fouls\s*Won\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star\s*NEW:\s*Combined\s*Player\s*Fouls\s*Committed\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star",
    r"icon-arrow-up\s*"  # Added this pattern to remove 'icon-arrow-up' with flexible spacing
]

# Function to clean unwanted text using regular expressions
def clean_text(content):
    for pattern in unwanted_text_patterns:
        content = re.sub(pattern, '', content)
    return content.strip()

# Function to get the adjusted combined section name
def get_combined_section_name(start_phrase):
    # Remove the first word from the first section name
    return " ".join(start_phrase.split(" ")[1:])

try:
    # Open and parse the HTML file
    with open(input_file_path, 'r', encoding='utf-8') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')

        # Function to extract text between start and end phrases
        def extract_section_text(start_phrase, end_phrase):
            section_start = soup.find(string=start_phrase)
            section_end = soup.find(string=end_phrase)

            if section_start and section_end:
                section_content = []
                for sibling in section_start.find_all_next(string=True):
                    if sibling == section_end:
                        break
                    section_content.append(sibling.strip())
                return " ".join(section_content).strip()
            else:
                return None

        # Prepare text for output
        combined_section_texts = []
        dataframes = {}  # Dictionary to store DataFrames

        for i in range(0, len(sections), 2):
            # Get the start and end phrases for the current pair of sections
            start_phrase_1, end_phrase_1 = sections[i]
            start_phrase_2, end_phrase_2 = sections[i + 1] if i + 1 < len(sections) else (None, None)

            # Extract and clean text for the first section
            section_1_text = extract_section_text(start_phrase_1, end_phrase_1)
            cleaned_section_1_text = clean_text(section_1_text) if section_1_text else ""

            # Extract and clean text for the second section
            section_2_text = extract_section_text(start_phrase_2, end_phrase_2) if start_phrase_2 else None
            cleaned_section_2_text = clean_text(section_2_text) if section_2_text else ""

            # Combine the sections with the adjusted section name
            section_name = get_combined_section_name(start_phrase_1)
            combined_text = f"{section_name}:\n{cleaned_section_1_text} {cleaned_section_2_text}"

            # Store the combined section text
            combined_section_texts.append(combined_text)

            # Now, process each section into a DataFrame
            # Use regex to parse the data for each section
            pattern = r"([A-Za-z\s\-]+?)\s(\d+\+.*?)(\d+/\d+)"
            matches = re.findall(pattern, combined_text)

            # Convert to tabular format
            section_data = [[match[0].strip(), match[1].strip(), match[2].strip()] for match in matches]
            df = pd.DataFrame(section_data, columns=["Player Name", "Action", "Odds"])

            # Store in dictionary with section name as key (replace spaces with underscores)
            dataframes[section_name.replace(" ", "_")] = df

        # Output the dataframes for each section
        for section_name, df in dataframes.items():
            print(f"{section_name}:")
            print(df)
            print("\n" + "="*50 + "\n")

except FileNotFoundError:
    print(f"Error: The file at {input_file_path} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Assuming the DataFrame for "Player Shots On Target" is in the `dataframes` dictionary
#df = dataframes["Player_Shots_On_Target"]

# Filter for rows where Player Name is "Jean-Philippe Mateta" and Action contains "1+"
#filtered_df = df[(df["Player Name"] == "Jean-Philippe Mateta") & (df["Action"].str.contains("1+"))]

# Extract and print the Odds
#odds = filtered_df["Odds"].iloc[0]  # Get the first matching odds
#print(odds)

# Print the names of all dataframes
print("Available DataFrame Names:")
for section_name in dataframes.keys():
    print(f"- {section_name}")