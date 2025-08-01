import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

def clean_action_column(action):
    """Transform the Action column text based on its content."""
    match = re.match(r"(At Least|Over) (\d+) (.+)", action)
    if match:
        qualifier = match.group(1)  # "At Least" or "Over"
        number = int(match.group(2))
        remainder = match.group(3)  # The rest of the action text

        if qualifier == "At Least":
            return f"{number}+ {remainder}"
        elif qualifier == "Over":
            return f"{number + 1}+ {remainder}"
    return action

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Path to your ChromeDriver (using raw string to avoid issues with backslashes)
driver_path = r"C:\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"
service = Service(driver_path)

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Target URL
url = "https://sports.williamhill.com/betting/en-gb/football/OB_EV33892092/aston-villa-vs-west-ham"

try:
    # Open the website
    driver.get(url)
    time.sleep(1)  # Wait for the page to fully load

    # 1. Find the element with data-marketcollectionid="4" and click on the corresponding href
    link = driver.find_element(By.XPATH, "//a[@data-marketcollectionid='4']")
    link.click()
    time.sleep(1)  # Wait for the page to load after the click

    # 2. Find all div elements with class 'header__toolbar' and trigger the dropdowns
    toolbar_divs = driver.find_elements(By.CLASS_NAME, "header__toolbar")

    # Iterate over each div and find the anchor tag to trigger the dropdown
    for toolbar_div in toolbar_divs:
        try:
            # Find the anchor tag within the div
            dropdown_button = toolbar_div.find_element(By.CSS_SELECTOR, "a.button-clear")

            # Click the button to expand the dropdown using JavaScript
            driver.execute_script("arguments[0].click();", dropdown_button)
            time.sleep(1)  # Wait for the dropdown to expand and content to load

        except Exception as e:
            # If no anchor tag is found or an error occurs, skip this div
            print(f"Error with toolbar div: {e}")
            continue

    # After expanding all dropdowns, extract the text from the body of the page
    page_text = driver.find_element(By.TAG_NAME, "body").text

    # Define the headers for filtering
    header_pairs = [
        ("Total Player Shots On Target", "1st Half Player Shots On Target"),
        ("Total Player Fouls", "Total Player Offsides"),
        ("Total Player Shots", "Player Shot In Both Halves"),
        ("Total Player Tackles", "1st Half Player Tackles")
    ]

    # Define the section names
    section_names = [
        "Total Player Shots On Target",
        "Total Player Fouls",
        "Total Player Shots",
        "Total Player Tackles"
    ]

    # Filter the content between the specified header pairs
    filtered_sections = {}
    for idx, (start_header, end_header) in enumerate(header_pairs):
        match = re.search(rf"({re.escape(start_header)}.*?{re.escape(end_header)})", page_text, re.DOTALL)
        if match:
            filtered_sections[section_names[idx]] = match.group(1)

    # Remove the lines containing the unwanted phrases
    unwanted_phrases = [
        "1st Half Player Shots On Target",
        "Total Player Offsides",
        "Player Shot In Both Halves",
        "1st Half Player Tackles"
    ]

    # Process each section to remove unwanted phrases and exclude the section name in the content
    final_filtered_text = ""
    for section_name, section_text in filtered_sections.items():
        # Remove the section name from the text itself
        section_text = section_text.replace(section_name, "").strip()

        # Remove lines with unwanted phrases
        filtered_lines = []
        for line in section_text.split("\n"):
            if not any(phrase in line for phrase in unwanted_phrases):
                filtered_lines.append(line)

        # Add section name and the cleaned-up text to the final output
        final_filtered_text += f"\n{section_name}\n"
        final_filtered_text += "\n".join(filtered_lines)
        final_filtered_text += "\n"

    # Save the filtered text to a file
    with open("final_filtered_text_with_sections.txt", "w", encoding="utf-8") as file:
        file.write(final_filtered_text)

    # Convert filtered text to DataFrames
    dataframes = {}
    for section_name, section_text in filtered_sections.items():
        lines = [line.strip() for line in section_text.split("\n") if line.strip()]

        players, actions, odds = [], [], []
        for i in range(len(lines) - 1):
            # Check if the current line contains player and action, and the next line contains odds
            match_player_action = re.match(r"(.+?)(At Least.*|Over.*)", lines[i])
            match_odds = re.match(r"(\d+/\d+)", lines[i + 1])

            if match_player_action and match_odds:
                players.append(match_player_action.group(1).strip())
                actions.append(match_player_action.group(2).strip())
                odds.append(match_odds.group(1).strip())

        # Create DataFrame for the section
        df = pd.DataFrame({"Player": players, "Action": actions, "Odds": odds})

        # Clean the Action column
        df["Action"] = df["Action"].apply(clean_action_column)

        # Store the DataFrame in the dictionary
        dataframes[section_name] = df

    # Print the DataFrames
    for name, df in dataframes.items():
        print(f"\n{name}:")
        print(df)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the browser
    driver.quit()