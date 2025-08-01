import pandas as pd
import re
from bs4 import BeautifulSoup
from tabulate import tabulate
import math
import fractions

# Go to the websites, make sure to open all relevant sections we want to scrape, then download the page as a HTML file and use this for scraping
bet365_file_path = r"C:\Users\zakaa\Downloads\Python Arbitrage\leiarsbet365.html"
skybet_file_path = r"C:\Users\zakaa\Downloads\Python Arbitrage\Leicester v Arsenal Betting & Odds » Sky Bet.html"

# Bet365 Scraping:
# Define the start and end phrases for each section to scrape
bet365_sections = [
    ("Player Shots On Target Over/Under", "Player Shots Over/Under"),
    ("Player Shots Over/Under", "Player Fouls Over/Under"),
    ("Player Fouls Over/Under", "Player Tackles Over/Under"),
    ("Player Tackles Over/Under", "Player Passes"),
]

# remove the text that we don't want (this is specific to the bet365 website)

def bet365_clean_text(text):
    text = text.replace("BB", "") # remove the BB which stands for Bet Builder
    text = text.replace("Over", " Over").replace("Under", " Under") # just adding spaces before "Over" and "Under"
    parts = text.split(" Over", 1) # splits the text at the first occurence of the word "Over"
    # there are also shirt numbers on the bet365 website, the following if function removes these:
    if len(parts) > 1:
        parts[0] = re.sub(r'\d+', '', parts[0])
        text = " Over".join(parts)
    return text.strip() # remove any whitespaces and return the cleaned text

try:
    with open(bet365_file_path, 'r', encoding='utf-8') as html_file:
        bet365_soup = BeautifulSoup(html_file, 'html.parser') # parse the HTML file's content using BeautifulSoup
        bet365_dataframes = {} # initialise dictionary for dataframes

        # look through HTML file for the section names we have already defined:
        for start_phrase, end_phrase in bet365_sections:
            section_start = bet365_soup.find(string=start_phrase)
            section_end = bet365_soup.find(string=end_phrase)

            if section_start and section_end: # if section_start and section_end both exist
                section_content = [] # initialise empty string for the section content
                for sibling in section_start.find_all_next(string=True):
                    if sibling == section_end:
                        break
                    section_content.append(sibling.strip()) # iterate through all text between the start and end phrase, and append them into section_content

                full_section_text = " ".join(section_content).strip() # collects all text into a single string, and removes whitespaces
                full_section_text = bet365_clean_text(full_section_text) # applies bet_365_clean_text function to clean the text

                # it is difficult to separate names based on regex formats, so we split them based on the HTML div classes:
                names = [] # initialise empty string for the names
                section_div = section_start.find_parent()
                if section_div:
                    name_divs = section_div.find_all('div', class_="srb-ParticipantLabelWithTeam_Name") # this is the div class containining the names
                    names = [div.get_text(strip=True) for div in name_divs] # add all names into the list

                names_text = re.sub(r'\s+', ' ', " ".join(names)) # combines all elements in the names list into a single string, separated by a space

                # we want to split the text, so that the names are on the first line, the odds for "Over" on the second, and odds for "Under" on the third
                # this is so it becomes easy to create the dataframe in the end
                # the following split_text function does exactly this:

                def split_text(input_text):
                    formatted_text = input_text.replace(" Over", "\nOver").replace(" Under", "\nUnder")
                    formatted_text = '\n'.join(line.rstrip() for line in formatted_text.split('\n'))
                    formatted_text = f"\n{formatted_text}\n"
                    return formatted_text

                given_text = full_section_text
                result = split_text(given_text) # applies the formatting to the full section text from scraping the HTML file

                original_text = result

                # now we actually split the text into 3 lines, so it is ready for making a DataFrame:
                lines = original_text.splitlines() # the splitlines() method splits a string into a list of lines
                player_names = lines[1].split("   ") # player names on line 1
                over_odds = lines[2].replace("Over", "").strip().split() # over odds on line 2
                under_odds = lines[3].replace("Under", "").strip().split() # under odds on line 3

                # now we create the dataframe:
                data = [] # initialise an empty list for holding the dictionaries for each player
                for i, name in enumerate(player_names): # iterates through player names, i is the index of the current player in the list, name is the actual name
                    over_index = i * 2
                    under_index = i * 2 # each odds is a number followed by a fraction, so there are two parts, which is why each index for the odds skips two

                    if over_index + 1 < len(over_odds) and under_index + 1 < len(under_odds): # validates there are enough elements in the odds sections
                        # create a dictionary for the current player, and append it to the data list (this is to create the Dataframe):
                        data.append({
                            "Player": name,
                            "Over": f"{over_odds[over_index]} {over_odds[over_index + 1]}", # first part returns the number e.g. Over 0.5, second part returns the fractional odds
                            "Under": f"{under_odds[under_index]} {under_odds[under_index + 1]}"
                        })

                df = pd.DataFrame(data) # converts the 'data' list into a pandas DataFrame, where each row corresponds to a player and their odds
                bet365_dataframes[start_phrase] = df # Stores the DataFrame in the bet365_dataframes dictionary using the section's start_phrase as the key.

# error handling:
except FileNotFoundError:
    print(f"Error: The file at {bet365_file_path} was not found.") # if HTML file is not found
except Exception as e:
    print(f"An error occurred: {e}") # another exception occurred in the try block not already caught out

# SkyBet Scraping
# define the start and end phrases for each section to scrape
# on the SkyBet site they split it into 'Home' and 'Away' teams, so we will have to merge them to get the same formatted result as bet365
skybet_sections = [
    ("Home Player Shots On Target", "Away Player Shots On Target"),
    ("Away Player Shots On Target", "Home Player Fouls Committed"),
    ("Home Player Fouls Committed", "Away Player Fouls Committed"),
    ("Away Player Fouls Committed", "Home Player Total Shots"),
    ("Home Player Total Shots", "Away Player Total Shots"),
    ("Away Player Total Shots", "Home Player Tackles"),
    ("Home Player Tackles", "Away Player Tackles"),
    ("Away Player Tackles", "Home Player Offsides"),
]

# define the text patterns we want to clean, and use \s* to match any whitespaces combination that may be different across the HTML file
unwanted_text_patterns = [
    r"icon-arrow-up\s*-\s*Opta\s*collect\s*data\s*for\s*all\s*competitions\s*that\s*Sky\s*Bet\s*offer\s*stats\s*markets\s*on\.\s*Sky\s*Bet\s*will\s*always\s*reference\s*Opta\s*for\s*resulting\.",
    r"Show\s*Less\s*icon-arrow-up\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star",
    r"Full\s*market\s*rules\s*available\s*via\s*the\s*Help\s*and\s*Support\s*page\.",
    r"Home\s*Player\s*Fouls\s*Won\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star\s*Away\s*Player\s*Fouls\s*Won\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star\s*NEW:\s*Combined\s*Player\s*Fouls\s*Committed\s*icon-arrow-down\s*Icon\s*/\s*Toggle\s*/\s*Outlined\s*/\s*Star",
    r"icon-arrow-up\s*"
]

# cleans the text by removing the above text patterns:
def skybet_clean_text(content):
    for pattern in unwanted_text_patterns:
        content = re.sub(pattern, '', content)
    return content.strip()

def skybet_get_combined_section_name(start_phrase):
    return " ".join(start_phrase.split(" ")[1:]) # removes the first word of the string (specifically we want to remove the 'Home' and 'Away')

try:
    with open(skybet_file_path, 'r', encoding='utf-8') as html_file:
        skybet_soup = BeautifulSoup(html_file, 'html.parser') # parse the HTML file's content using BeautifulSoup
        skybet_combined_section_texts = [] # initialise for holding the combined section text
        skybet_dataframes = {} # initialise the dataframes

        for i in range(0, len(skybet_sections), 2): # iterates through the skybet sections in steps of 2
            start_phrase_1, end_phrase_1 = skybet_sections[i] # define the start and end markers for the first section
            start_phrase_2, end_phrase_2 = skybet_sections[i + 1] if i + 1 < len(skybet_sections) else (None, None) # Define the second section in the pair (if available)

            # now use BeautifulSoup to extract the text between the start_phrase and end_phrase, and store it in a similar way we did with bet365:
            def extract_section_text(start_phrase, end_phrase):
                section_start = skybet_soup.find(string=start_phrase)
                section_end = skybet_soup.find(string=end_phrase)

                if section_start and section_end:
                    section_content = []
                    for sibling in section_start.find_all_next(string=True):
                        if sibling == section_end:
                            break
                        section_content.append(sibling.strip())
                    return " ".join(section_content).strip()
                else:
                    return None

            section_1_text = extract_section_text(start_phrase_1, end_phrase_1)
            cleaned_section_1_text = skybet_clean_text(section_1_text) if section_1_text else "" # applies the cleaning function we define earlier on the extracted text

            section_2_text = extract_section_text(start_phrase_2, end_phrase_2) if start_phrase_2 else None
            cleaned_section_2_text = skybet_clean_text(section_2_text) if section_2_text else ""

            # combines the 'Home' and 'Away' sections into one section:
            section_name = skybet_get_combined_section_name(start_phrase_1)
            combined_text = f"{section_name}:\n{cleaned_section_1_text} {cleaned_section_2_text}"
            skybet_combined_section_texts.append(combined_text)

            # regex pattern to extract data:
            pattern = r"([A-Za-z\s\-]+?)\s(\d+\+.*?)(\d+/\d+)"
            # ([A-Za-z\s\-]+?) matches the player name
            # (\d+\+.*?) matches the action e.g. 1+ Shots on Target
            # (\d+/\d+) matches odds in the format "X/Y"
            matches = re.findall(pattern, combined_text) # finds all matches in combined_text

            section_data = [[match[0].strip(), match[1].strip(), match[2].strip()] for match in matches] # looks through matches, and match[0] is the player name
            # match[1] is the action, and match[2] is the odds. Strips them off any trailing whitespaces using .strip(), and creates a list of lists of data
            df = pd.DataFrame(section_data, columns=["Player Name", "Action", "Odds"]) # converts section_data into a pandas DataFrame with three columns
            skybet_dataframes[section_name.replace(" ", "_")] = df # store the DataFrame in a dictionary, and replace the spaces in the key names with underscore

# Error handling:
except FileNotFoundError:
    print(f"Error: The file at {skybet_file_path} was not found.") # if HTML file is not found
except Exception as e:
    print(f"An error occurred: {e}") # another exception occurred in the try block not already caught out 

# We want to rename the dataframes so we know what website they come from more clearly:
# Mapping of old bet365 section names to new names
bet365_rename_mapping = {
    "Player Shots On Target Over/Under": "bet365_Player_Shots_On_Target",
    "Player Shots Over/Under": "bet365_Player_Total_Shots",
    "Player Fouls Over/Under": "bet365_Player_Fouls_Committed",
    "Player Tackles Over/Under": "bet365_Player_Tackles"
}

# Rename the DataFrame keys in bet365_dataframes
bet365_dataframes_renamed = {
    bet365_rename_mapping.get(section_name, section_name): df
    for section_name, df in bet365_dataframes.items()
}

# Print the renamed DataFrames
for section_name, df in bet365_dataframes_renamed.items():
    print(f"{section_name}:")
    print(df)
    print("\n" + "="*50 + "\n")

# Rename the SkyBet DataFrames by adding the "sky_" prefix
skybet_dataframes_renamed = {
    f"sky_{section_name}": df
    for section_name, df in skybet_dataframes.items()
}

# For the SkyBet Fouls Committed DataFrame, the text "To Commit" gets placed in the 'Player Name' column, we want to remove this:
skybet_fouls_committed_df = skybet_dataframes_renamed["sky_Player_Fouls_Committed"]
skybet_fouls_committed_df["Player Name"] = skybet_fouls_committed_df["Player Name"].str.replace(" To Commit", "", regex=False)

# Print the renamed SkyBet DataFrames
for section_name, df in skybet_dataframes_renamed.items():
    print(f"{section_name}:")
    print(df)
    print("\n" + "="*50 + "\n")

# Now we have the DataFrames in the format we can compare odds for arbitrage possibilities

# First, we write a function to calculate the formula for ROI, which we will need to use later to find the profit we can make off arbitrage opportunities

# Function to convert fractional odds to decimal
def fractional_to_decimal(fraction):
    num, denom = map(int, fraction.split("/"))
    return 1 + (num / denom)

# Function to calculate the arbitrage ROI
def calculate_arbitrage_roi(stake, odds1, odds2):
    """
    Calculate the guaranteed ROI for an arbitrage opportunity.

    Parameters:
        stake (float): Total stake (e.g., £100).
        odds1 (str): Fractional odds for the first outcome (e.g., "2/11").
        odds2 (str): Fractional odds for the second outcome (e.g., "6/1").

    Returns:
        float: ROI percentage.
        float: Stake on Bet365.
        float: Stake on SkyBet.
        float: Total profit.
    """
    # Convert fractional odds to decimals
    decimal1 = fractional_to_decimal(odds1)
    decimal2 = fractional_to_decimal(odds2)

    # Calculate stakes for equal payouts
    stake1 = (decimal2 / (decimal1 + decimal2)) * stake
    stake2 = stake - stake1

    # Guaranteed payout
    payout = stake1 * decimal1  # or stake2 * decimal2, they will be the same

    # Calculate total profit
    total_profit = payout - stake

    # ROI calculation
    roi = (total_profit / stake) * 100
    return roi, stake1, stake2, total_profit

# Now we move on to working with the dataframes to extract the relevant odds and seek arbitrage opportunities:

# List of all dataframes to process
# Add a more readable and friendly description, so the first part of each item is the dataframe_key (the actual key) and the second part is the description
dataframes_to_process = [
    ("Player_Shots_On_Target", "Shots On Target"),
    ("Player_Total_Shots", "Total Shots"),
    ("Player_Fouls_Committed", "Fouls Committed"),
    ("Player_Tackles", "Tackles"),
]

# Iterate through each dataframe pair
for dataframe_key, description in dataframes_to_process:
    # Access Bet365 and SkyBet DataFrames
    bet365_df = bet365_dataframes_renamed[f"bet365_{dataframe_key}"]
    skybet_df = skybet_dataframes_renamed[f"sky_{dataframe_key}"]

    # Iterate through all rows (players) in the Bet365 DataFrame
    for _, row in bet365_df.iterrows():
        player_name = row["Player"]
        under_odds = row["Under"]

        # Step 1: Extract and round the number from Bet365 odds
        match = re.search(r"(\d+\.\d+)", under_odds)  # Find the first decimal number (e.g. 0.5 or 1.5)
        if match:
            first_number = float(match.group(1))
            rounded_number = int(-(-first_number // 1))  # Round up to the nearest whole number as skybet uses whole numbers, and we want to compare to skybet

            # Step 2: Search for this number in the SkyBet DataFrame using loc
            action_to_find = f"{rounded_number}"
            filtered_rows = skybet_df.loc[
                (skybet_df["Player Name"].str.lower() == player_name.lower()) &  # Match player name
                (skybet_df["Action"].str.contains(action_to_find, case=False, na=False))  # Match action
            ]

            if not filtered_rows.empty:
                # Step 3: Extract odds from Bet365 and SkyBet
                bet365_fractional_odds = re.search(r"(\d+/\d+)", under_odds).group(1) # extracts the first fraction from bet365 "Under", which will be the odds
                skybet_fractional_odds = filtered_rows.iloc[0]["Odds"] # skybet stores the odds by itself, so we can just use iloc[0] to access it

                # Step 4: Calculate ROI and suggested stakes
                roi, stake1, stake2, total_profit = calculate_arbitrage_roi(100, bet365_fractional_odds, skybet_fractional_odds)

                # Step 5: Check for arbitrage opportunity and display results
                if roi > 0:  # Arbitrage opportunity exists if ROI > 0
                    print(f"ARBITRAGE OPPORTUNITY - {description}")
                    print(f"Player: {player_name}")
                    print(f"Bet365 'Under' Odds: {bet365_fractional_odds}")
                    print(f"SkyBet Odds: {skybet_fractional_odds}")
                    print(f"Guaranteed ROI: {roi:.2f}%")
                    print(f"Suggested Bet on Bet365: £{stake1:.2f}")
                    print(f"Suggested Bet on SkyBet: £{stake2:.2f}")
                    print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
                    print("-" * 40)