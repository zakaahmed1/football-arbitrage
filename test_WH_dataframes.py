import re
import pandas as pd

# Sample section text
section_text = """
Gabriel Jesus At Least 1 Shot On Target
7/20
Gabriel Jesus Over 1 Shot On Target
29/20
Gabriel Jesus Over 2 Shots On Target
4/1
Gabriel Jesus Over 3 Shots On Target
10/1
Kai Havertz At Least 1 Shot On Target
2/5
Kai Havertz Over 1 Shot On Target
7/4
Kai Havertz Over 2 Shots On Target
5/1
Kai Havertz Over 3 Shots On Target
12/1
Leandro Trossard At Least 1 Shot On Target
4/9
Leandro Trossard Over 1 Shot On Target
19/10
Leandro Trossard Over 2 Shots On Target
11/2
Leandro Trossard Over 3 Shots On Target
12/1
"""

# Function to create a table from the section text
def create_table_from_section(section_text):
    # Split the section text into lines
    lines = section_text.strip().split("\n")

    # Initialize lists to hold the columns
    player_names = []
    actions = []
    odds = []

    # Iterate through the lines and organize the data into columns
    for i in range(0, len(lines), 2):
        # Split the first part to find where the action starts (either "At Least" or "Over")
        action_start = re.search(r"(At Least|Over)", lines[i])

        if action_start:
            # Get the player name by removing the action part
            player_name = lines[i][:action_start.start()].strip()
            
            # Get the action, which starts from the found "At Least" or "Over"
            action = lines[i][action_start.start():].strip()

            # Get the odds from the next line
            odds_value = lines[i + 1]

            # Append to the lists
            player_names.append(player_name)
            actions.append(action)
            odds.append(odds_value)
    
    # Create a DataFrame from the columns
    df = pd.DataFrame({
        "Player": player_names,
        "Action": actions,
        "Odds": odds
    })
    
    return df

# Call the function with the sample section text
df = create_table_from_section(section_text)

# Print the table
print(df)

# Optionally, save the DataFrame to a CSV file
df.to_csv("player_shots_on_target.csv", index=False)
