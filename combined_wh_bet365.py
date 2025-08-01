import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# William Hill Scraping Code:

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Path to your ChromeDriver
driver_path = r"C:\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"
service = Service(driver_path)

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Target URL
url = "https://sports.williamhill.com/betting/en-gb/football/OB_EV33892092/aston-villa-vs-west-ham"

try:
    driver.get(url)
    time.sleep(1)

    link = driver.find_element(By.XPATH, "//a[@data-marketcollectionid='4']")
    link.click()
    time.sleep(1)

    toolbar_divs = driver.find_elements(By.CLASS_NAME, "header__toolbar")

    for toolbar_div in toolbar_divs:
        try:
            dropdown_button = toolbar_div.find_element(By.CSS_SELECTOR, "a.button-clear")
            driver.execute_script("arguments[0].click();", dropdown_button)
            time.sleep(1)
        except Exception as e:
            print(f"Error with toolbar div: {e}")
            continue

    page_text = driver.find_element(By.TAG_NAME, "body").text

    header_pairs = [
        ("Total Player Shots on Target", "Player to Score or Assist"),
        ("Total Player Fouls", "To Score a Header"),
        ("Total Player Shots", "Player Shot In Both Halves"),
        ("Total Player Tackles", "1st Half Player Tackles")
    ]

    section_names = [
        "Total Player Shots on Target",
        "Total Player Fouls",
        "Total Player Shots",
        "Total Player Tackles"
    ]

    filtered_sections = {}
    for idx, (start_header, end_header) in enumerate(header_pairs):
        match = re.search(rf"({re.escape(start_header)}.*?{re.escape(end_header)})", page_text, re.DOTALL)
        if match:
            filtered_sections[section_names[idx]] = match.group(1)

    unwanted_phrases = [
        "Player to Score or Assist",
        "To Score a Header",
        "Player Shot In Both Halves",
        "1st Half Player Tackles"
    ]

    dataframes = {}

    for section_name, section_text in filtered_sections.items():
        section_text = section_text.replace(section_name, "").strip()

        filtered_lines = []
        for line in section_text.split("\n"):
            if not any(phrase in line for phrase in unwanted_phrases):
                filtered_lines.append(line)

        rows = []
        for i, line in enumerate(filtered_lines):
            if i % 2 == 0:
                player_action_line = line
                odds_line = filtered_lines[i + 1] if i + 1 < len(filtered_lines) else ""

                match = re.match(r"(.+?)(At Least.*|Over.*)", player_action_line)
                if match:
                    player_name = match.group(1).strip()
                    action = match.group(2).strip()

                    odds_match = re.search(r"(\d+/\d+)", odds_line)
                    odds = odds_match.group(1) if odds_match else ""

                    rows.append([player_name, action, odds])

        df = pd.DataFrame(rows, columns=["Player", "Action", "Odds"])

        df["Action"] = df["Action"].apply(lambda x: "{}+ Shots On Target".format(int(re.search(r"\d+", x).group()) + (1 if "Over" in x else 0)))

        dataframes[section_name] = df

    rename_mapping = {
        "Total Player Shots on Target": "wh_Player_Shots_On_Target",
        "Total Player Fouls": "wh_Player_Fouls_Committed",
        "Total Player Shots": "wh_Player_Total_Shots",
        "Total Player Tackles": "wh_Player_Tackles"
    }

    dataframes = {rename_mapping.get(key, key): df for key, df in dataframes.items()}

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()

# Bet365 Scraping Code:

file_path = r"C:\Users\zakaa\Downloads\Python Arbitrage\astwhubet365.html"

def clean_text(text):
    text = text.replace("BB", "")
    text = text.replace("Over", " Over").replace("Under", " Under")
    parts = text.split(" Over", 1)
    if len(parts) > 1:
        parts[0] = re.sub(r'\d+', '', parts[0])
        text = " Over".join(parts)
    return text.strip()

def split_text(input_text):
    formatted_text = input_text.replace(" Over", "\nOver").replace(" Under", "\nUnder")
    formatted_text = '\n'.join(line.rstrip() for line in formatted_text.split('\n'))
    return f"\n{formatted_text}\n"

def process_section(soup, start_phrase, end_phrase):
    section_start = soup.find(string=start_phrase)
    section_end = soup.find(string=end_phrase)

    if not (section_start and section_end):
        return None

    section_content = []
    for sibling in section_start.find_all_next(string=True):
        if sibling == section_end:
            break
        section_content.append(sibling.strip())

    full_section_text = clean_text(" ".join(section_content).strip())

    section_div = section_start.find_parent()
    names = []
    if section_div:
        name_divs = section_div.find_all('div', class_="srb-ParticipantLabelWithTeam_Name")
        names = [div.get_text(strip=True) for div in name_divs]

    names_text = re.sub(r'\s+', ' ', " ".join(names))
    formatted_text = split_text(full_section_text)

    lines = formatted_text.splitlines()
    if len(lines) < 4:
        return None

    player_names = lines[1].split("   ")
    over_odds = lines[2].replace("Over", "").strip().split()
    under_odds = lines[3].replace("Under", "").strip().split()

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

        sections = [
            ("Player Shots On Target Over/Under", "Player Shots Over/Under"),
            ("Player Shots Over/Under", "Player Fouls Committed"),
            ("Player Fouls Committed", "Player Tackles"),
            ("Player Tackles", "Player Passes"),
        ]

        dataframes_bet365 = {}
        for start_phrase, end_phrase in sections:
            df = process_section(soup, start_phrase, end_phrase)
            if df is not None:
                dataframes_bet365[start_phrase] = df

        rename_mapping_bet365 = {
            "Player Shots On Target Over/Under": "bet365_Player_Shots_On_Target",
            "Player Shots Over/Under": "bet365_Player_Total_Shots",
            "Player Fouls Committed": "bet365_Player_Fouls_Committed",
            "Player Tackles": "bet365_Player_Tackles"
        }

        dataframes_bet365 = {rename_mapping_bet365.get(key, key): df for key, df in dataframes_bet365.items()}

except FileNotFoundError:
    print(f"Error: The file at {file_path} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Outputting the DataFrames from both William Hill and Bet365
print("\n=== William Hill DataFrames ===\n")
for name, df in dataframes.items():
    print(f"{name}:")
    print(df)
    print("\n" + "=" * 50 + "\n")

print("\n=== Bet365 DataFrames ===\n")
for name, df in dataframes_bet365.items():
    print(f"{name}:")
    print(df)
    print("\n" + "=" * 50 + "\n")

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