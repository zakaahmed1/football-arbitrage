from bs4 import BeautifulSoup
import pandas as pd

# Path to the local HTML file
html_file_path = r"C:\Users\zakaa\Downloads\Brentford - Arsenal Betting Odds, Football Betting at Betway.html"

# Open and read the HTML file
with open(html_file_path, "r", encoding="utf-8") as file:
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
    
    # Print the table for this section
    print(f"Section: {section_name}\n")
    print(df)
    print("\n" + "-"*80 + "\n")