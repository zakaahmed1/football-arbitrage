import pandas as pd
from bs4 import BeautifulSoup
import re
import numpy as np
from fractions import Fraction

# Go to the websites, make sure to open all relevant sections we want to scrape, then download the page as a HTML file and use this for scraping
bet365_file_path = r"C:\Users\zakaa\Downloads\Python Arbitrage\totlivbet365.html"
betway_file_path = r"C:\Users\zakaa\Downloads\Python Arbitrage\Tottenham - Liverpool Betting Odds, Football Betting at Betway.html"

# Bet365 Scraping
def scrape_bet365(file_path):
    # Function to clean text (remove BB and numbers before "Over")
    def clean_text(text):
        text = text.replace("BB", "")  # Remove 'BB'
        text = text.replace("Over", " Over").replace("Under", " Under")  # Add space before "Over" and "Under"
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

            # Process each section and store the dataframes in a dictionary
            dataframes = {}
            for start_phrase, end_phrase in sections:
                df = process_section(soup, start_phrase, end_phrase)
                if df is not None:
                    # Rename the dataframes according to the provided names
                    if start_phrase == "Player Shots On Target Over/Under":
                        dataframes["Player_Shots_On_Target"] = df
                    elif start_phrase == "Player Shots Over/Under":
                        dataframes["Player_Total_Shots"] = df
                    elif start_phrase == "Player Fouls Committed":
                        dataframes["Player_Fouls_Committed"] = df
                    elif start_phrase == "Player Tackles":
                        dataframes["Player_Tackles"] = df

            return dataframes

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

# Betway Scraping
def scrape_betway(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    all_text = soup.get_text(separator="\n", strip=True)

    start_marker = "Player To Have"
    end_marker = "Player To Score Or Assist"
    lines = all_text.splitlines()

    sections = []
    section_names = []
    current_section_name = ""
    current_section_text = []
    inside_section = False

    for line in lines:
        if line.startswith(start_marker):
            if current_section_name:
                sections.append((current_section_name, "\n".join(current_section_text)))
            current_section_name = line.strip()
            section_names.append(current_section_name)
            current_section_text = []
            inside_section = True
        elif end_marker in line and inside_section:
            sections.append((current_section_name, "\n".join(current_section_text)))
            inside_section = False
        if inside_section:
            current_section_text.append(line.strip())

    dataframes = {}
    for section_name, section_content in sections:
        cleaned_lines = [
            line.replace("Cash Out", "").strip()
            for line in section_content.splitlines() if "Suspended" not in line
        ]
        cleaned_lines = cleaned_lines[3:] if len(cleaned_lines) > 3 else []
        players, actions, odds = [], [], []

        for i in range(0, len(cleaned_lines), 2):
            if i + 1 < len(cleaned_lines):
                players.append(cleaned_lines[i])
                actions.append(section_name)
                odds.append(cleaned_lines[i + 1])

        # Create a DataFrame for the section and store it in the dictionary with the section name
        df = pd.DataFrame({'Player Name': players, 'Action': actions, 'Odds': odds})
        dataframes[section_name] = df

    return dataframes

# Scrape Bet365
bet365_dataframes = scrape_bet365(bet365_file_path)
print("Bet365 Data:")
for section_name, df in bet365_dataframes.items():
    print(f"{section_name}")
    print(df)
    print("\n" + "=" * 50 + "\n")

# Scrape Betway
print("Betway Data:")

# Open and read the HTML file
with open(betway_file_path, "r", encoding="utf-8") as file:
    html_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")

# Extract all visible text
all_text = soup.get_text(separator="\n", strip=True)

# Define the markers
start_marker = "Player To Have"
end_marker = "Player To Score Or Assist"

# Split the text into lines for easier processing
lines = all_text.splitlines()

# Temporary variables to hold the current section name and content
sections = []
section_names = []  # List to hold the section names
current_section_name = ""
current_section_text = []
inside_section = False

# Iterate through lines to detect and extract text between the markers
for line in lines:
    if line.startswith(start_marker):
        # If the line starts with "Player To Have", it's a new section name
        if current_section_name:
            sections.append((current_section_name, "\n".join(current_section_text)))  # Store the previous section content
        current_section_name = line.strip()  # Capture the new section name
        section_names.append(current_section_name)  # Add section name to the list
        current_section_text = []  # Reset the content for the new section
        inside_section = True

    elif end_marker in line and inside_section:
        # Stop capturing text once we hit the end marker
        sections.append((current_section_name, "\n".join(current_section_text)))  # Store the last section content
        inside_section = False

    if inside_section:
        # Add the line to the current section's content
        current_section_text.append(line.strip())

# Initialize the global dictionary to store the cleaned DataFrames
betway_dataframes = {}

# Clean and format the sections into a table
for section_name, section_content in sections:
    # Clean the section content
    cleaned_section_content = section_content.replace("Cash Out", "")

    # Remove lines containing "Suspended"
    cleaned_lines = [
        line for line in cleaned_section_content.splitlines() if "Suspended" not in line
    ]

    # Remove the section name from the content, if it appears
    cleaned_section_content = "\n".join(cleaned_lines).replace(section_name, "").strip()

    # Remove the first three lines
    cleaned_lines = cleaned_section_content.splitlines()[2:]  # Skip the first three lines
    cleaned_section_content = "\n".join(cleaned_lines)

    # Identify and remove the first line of consecutive lines of just text
    final_lines = []
    prev_line_is_text = False

    for line in cleaned_section_content.splitlines():
        if line and not any(char.isdigit() for char in line):  # If the line is just text (no numbers)
            if prev_line_is_text:
                # Remove the previous line (the first of the consecutive lines)
                final_lines.pop()
            prev_line_is_text = True
        else:
            prev_line_is_text = False

        final_lines.append(line)

    # Create the table for each section
    players = []
    actions = []
    odds = []

    # Pair up players and odds
    for i in range(0, len(final_lines), 2):
        if i + 1 < len(final_lines):
            player_name = final_lines[i].strip()
            player_odds = final_lines[i + 1].strip()
            players.append(player_name)
            actions.append(section_name)
            odds.append(player_odds)

    # Create a DataFrame for the section
    df = pd.DataFrame({
        'Player Name': players,
        'Action': actions,
        'Odds': odds
    })

    # Add the cleaned DataFrame to the global dictionary
    betway_dataframes[section_name] = df

    # Print the table for this section
    print(f"{section_name}\n")
    print(df)
    print("\n" + "-" * 80 + "\n")

def multiply_fractions(fraction1, fraction2):
    """Multiply two fractional odds and return the result as a fraction."""
    try:
        frac1 = Fraction(fraction1)
        frac2 = Fraction(fraction2)
        return frac1 * frac2
    except ValueError:
        return None

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
        float: Stake on Betway 
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

# Step 1: Access the Bet365 Player_Shots_On_Target dataframe
bet365_player_shots_on_target = bet365_dataframes["Player_Shots_On_Target"]

# Step 2: Iterate over all players in the Bet365 Player_Shots_On_Target dataframe
for _, row in bet365_player_shots_on_target.iterrows():
    player_name = row['Player']
    under_odds = row['Under']

    # Skip if under odds are missing or not in the expected format
    if not under_odds or ' ' not in under_odds:
        continue

    # Extract the decimal and fractional parts of the "Under" column
    try:
        decimal_number = float(under_odds.split()[0])  # First part is the decimal number
        fractional_odds = under_odds.split()[1]  # Second part is the fractional odds
    except (ValueError, IndexError):
        continue

    # Round up the decimal number
    rounded_up_number = int(np.ceil(decimal_number))
    rounded_up_number_str = str(rounded_up_number)

    # Step 3: Search for the matching Betway section for "Shots On Target"
    betway_match_found = False
    for section_name, betway_df in betway_dataframes.items():
        if f"Player To Have {rounded_up_number_str}+ Shots On Target" in section_name:
            # Clean up player names in the Betway dataframe for consistent matching
            betway_df['Player Name'] = betway_df['Player Name'].str.strip()

            # Find the row in the Betway dataframe for the current player
            betway_row = betway_df[betway_df['Player Name'] == player_name]

            if not betway_row.empty:
                # Multiply fractional odds
                product_fraction = multiply_fractions(fractional_odds, betway_row['Odds'].iloc[0])

                # Check if there is an arbitrage opportunity
                if product_fraction and product_fraction > 1:
                    # Calculate the arbitrage ROI
                    stake = 100  # Assume a £100 stake for the calculation
                    roi, stake1, stake2, total_profit = calculate_arbitrage_roi(stake, fractional_odds, betway_row['Odds'].iloc[0])
                    
                    # Print only if there is an arbitrage opportunity
                    print(f"ARBITRAGE OPPORTUNITY! - Shots On Target")
                    print(f"Player: {player_name}")
                    print(f"Bet365 'Under' Odds: {fractional_odds}")
                    print(f"Betway Odds: {betway_row['Odds'].iloc[0]}")
                    print(f"Guaranteed ROI: {roi:.2f}%")
                    print(f"Suggested bet on Bet365: £{stake1:.2f}")
                    print(f"Suggested bet on Betway: £{stake2:.2f}")
                    print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
                    print("-" * 40)
                betway_match_found = True
                break

    # Step 4: Handle case where no match is found (no output if no arbitrage)
    if not betway_match_found:
        continue

# Step 1: Access the Bet365 Player_Total_Shots dataframe
bet365_player_total_shots = bet365_dataframes["Player_Total_Shots"]

# Step 2: Iterate over all players in the Bet365 Player_Total_Shots dataframe
for _, row in bet365_player_total_shots.iterrows():
    player_name = row['Player']
    under_odds = row['Under']

    # Skip if under odds are missing or not in the expected format
    if not under_odds or ' ' not in under_odds:
        continue

    # Extract the decimal and fractional parts of the "Under" column
    try:
        decimal_number = float(under_odds.split()[0])  # First part is the decimal number
        fractional_odds = under_odds.split()[1]  # Second part is the fractional odds
    except (ValueError, IndexError):
        print(f"Error parsing Under odds for Player: {player_name}, Odds: {under_odds}")
        continue

    # Round up the decimal number
    rounded_up_number = int(np.ceil(decimal_number))
    rounded_up_number_str = str(rounded_up_number)

    # Step 3: Search for the matching Betway section for "Shots"
    betway_match_found = False
    for section_name, betway_df in betway_dataframes.items():
        if section_name == f"Player To Have {rounded_up_number_str}+ Shots":
            # Clean up player names in the Betway dataframe for consistent matching
            betway_df['Player Name'] = betway_df['Player Name'].str.strip()

            # Find the row in the Betway dataframe for the current player
            betway_row = betway_df[betway_df['Player Name'] == player_name]

            if not betway_row.empty:
                # Multiply fractional odds
                product_fraction = multiply_fractions(fractional_odds, betway_row['Odds'].iloc[0])

                # Check if there is an arbitrage opportunity
                if product_fraction and product_fraction > 1:
                    # Print Bet365 and Betway match
                    print(f"ARBITRAGE OPPORTUNITY! - Shots")
                    print(f"Player: {player_name}")
                    print(f"Bet365 'Under' Odds: {fractional_odds}")
                    print(f"Betway Odds: {betway_row['Odds'].iloc[0]}")
                    # Calculate the arbitrage ROI
                    stake = 100  # Assume a £100 stake for the calculation
                    roi, stake1, stake2, total_profit = calculate_arbitrage_roi(stake, fractional_odds, betway_row['Odds'].iloc[0])
                    print(f"Guaranteed ROI: {roi:.2f}%")
                    print(f"Suggested Bet on Bet365: £{stake1:.2f}")
                    print(f"Suggested Bet on Betway: £{stake2:.2f}")
                    print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
                    print("-" * 40)

                betway_match_found = True
                break