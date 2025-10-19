# bet365_betway_arbitrage.py

import re
import math
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from fractions import Fraction

# =========================================================
# 0) CONFIG: set these to your saved HTML files
# =========================================================
bet365_file_path = r"C:\Users\AhmedZ\Downloads\whubre365.html"
betway_file_path = r"C:\Users\AhmedZ\Downloads\whubrebw.html"

# =========================================================
# 1) BET365 SCRAPING — exact section titles (Over/Under cards)
#    Returns dict with keys:
#       Player_Shots_On_Target | Player_Total_Shots | Player_Fouls_Committed | Player_Tackles
#    Each DataFrame: columns ["Player", "Over", "Under"] with values like "Under 0.5 4/6"
# =========================================================

BET365_EXACT_TITLES = {
    "Player_Shots_On_Target": "Player Shots On Target Over/Under",
    "Player_Total_Shots":     "Player Shots Over/Under",
    "Player_Fouls_Committed": "Player Fouls Over/Under",
    "Player_Tackles":         "Player Tackles Over/Under",
}

_FRACT_RE = re.compile(r"(?:\d+/\d+|EVS|Evens|EVENS)", re.I)

def _norm_frac(s: str) -> str:
    s = s.strip().upper()
    return "1/1" if s in {"EVS", "EVENS"} else s.lower()

def _title_of(mg):
    t = mg.find("div", class_="gl-MarketGroup_Name")
    if not t:
        t = mg.find("div", class_="cm-MarketGroupWithIconsButton_Text")
    return t.get_text(strip=True) if t else ""

def _b365_extract_names(market_root):
    return [
        div.get_text(strip=True)
        for div in market_root.find_all("div", class_="srb-ParticipantLabelWithTeam_Name")
    ]

def _b365_extract_cells(market_root):
    """
    Return ordered list of (handicap, odds) cells.
    Prefer CenteredStacked (handicap + odds); fallback to odds-only if needed.
    """
    cells = []
    for cell in market_root.find_all("div", class_="gl-ParticipantCenteredStacked"):
        h = cell.find("span", class_="gl-ParticipantCenteredStacked_Handicap")
        o = cell.find("span", class_="gl-ParticipantCenteredStacked_Odds")
        if h and o:
            cells.append((h.get_text(strip=True), o.get_text(strip=True)))
    if not cells:
        for oo in market_root.find_all("span", class_="gl-ParticipantOddsOnly_Odds"):
            cells.append(("", oo.get_text(strip=True)))
    return cells

def _b365_extract_market_df(market_root, label_text: str):
    """
    Build DataFrame with columns: Player | {label_text}
    Row example: "Over 0.5 10/11" or "Under 1.5 4/5".
    """
    names = _b365_extract_names(market_root)
    cells = _b365_extract_cells(market_root)
    n = min(len(names), len(cells))
    rows = []
    for i in range(n):
        player = names[i]
        hc, ov = cells[i]
        rows.append({"Player": player, label_text: f"{label_text} {hc} {ov}".strip()})
    return pd.DataFrame(rows, columns=["Player", label_text])

def scrape_bet365(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as html_file:
            soup = BeautifulSoup(html_file, 'html.parser')

        market_groups = soup.find_all("div", class_="gl-MarketGroup")
        out = {}

        # For each exact market title T, look for exact cards:
        #   T,  T - Over,  T - Under
        for key_name, exact_title in BET365_EXACT_TITLES.items():
            over_df = under_df = combined_df = None

            for mg in market_groups:
                title = _title_of(mg)
                if title == exact_title + " - Over":
                    over_df = _b365_extract_market_df(mg, "Over")
                elif title == exact_title + " - Under":
                    under_df = _b365_extract_market_df(mg, "Under")
                elif title == exact_title:
                    combined_df = _b365_extract_market_df(mg, "Over_Under_RAW")

                if over_df is not None and under_df is not None:
                    break

            if over_df is None and under_df is None and combined_df is not None:
                # Split combined card into Over/Under halves by number of names/cells
                names = combined_df["Player"].tolist()
                mg_combined = next((mg for mg in market_groups if _title_of(mg) == exact_title), None)
                if mg_combined:
                    cells = _b365_extract_cells(mg_combined)
                    N = len(names)
                    if N and len(cells) >= 2 * N:
                        over_cells = cells[:N]
                        under_cells = cells[N:2 * N]
                        over_df = pd.DataFrame({
                            "Player": names,
                            "Over": [f"Over {h} {o}".strip() for (h, o) in over_cells]
                        })
                        under_df = pd.DataFrame({
                            "Player": names,
                            "Under": [f"Under {h} {o}".strip() for (h, o) in under_cells]
                        })

            if over_df is not None and "Over" in over_df.columns and under_df is not None and "Under" in under_df.columns:
                merged = pd.merge(over_df, under_df, on="Player", how="inner")
            elif over_df is not None:
                merged = over_df.copy(); merged["Under"] = ""
            elif under_df is not None:
                merged = under_df.copy(); merged["Over"] = ""
            else:
                merged = pd.DataFrame(columns=["Player", "Over", "Under"])

            out[key_name] = merged[["Player", "Over", "Under"]]

        return out

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

# =========================================================
# 2) BETWAY SCRAPING — paired-row table layout
#    Returns dict of DataFrames keyed by exact section title strings:
#       "Player To Have 1+ Shots", "Player To Have 2+ Shots", ...,
#       "Player To Have 1+ Shots On Target", ...
# =========================================================

def scrape_betway(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    dataframes = {}

    # Each market has a header: [data-testid="table-header-title"]
    for header in soup.select('[data-testid="table-header"] [data-testid="table-header-title"]'):
        section_title = header.get_text(strip=True)
        if not section_title.startswith("Player To Have"):
            continue

        # Table lives in the same market-table-section
        section = header.find_parent(attrs={"data-testid": "market-table-section"})
        if not section:
            continue
        table = section.select_one("table")  # class names change; tag stays table
        if not table:
            continue

        rows = table.select("tbody > tr")
        players, actions, odds = [], [], []

        i = 0
        while i < len(rows):
            # Row of two names
            name_cells = rows[i].select("td")
            left_name = name_cells[0].get_text(strip=True) if len(name_cells) >= 1 else ""
            right_name = name_cells[1].get_text(strip=True) if len(name_cells) >= 2 else ""

            # Next row: two odds buttons
            left_odds = right_odds = ""
            if i + 1 < len(rows):
                odds_cells = rows[i+1].select("td")

                def extract_price(td):
                    # Prefer explicit price span
                    span = td.select_one('[data-testid="outcome-price-value"]')
                    if span and span.get_text(strip=True):
                        return span.get_text(strip=True)
                    # Fallback to attribute (e.g., "Callum Wilson 3/8")
                    btn = td.select_one('[data-testid="outcome"]')
                    if btn and btn.has_attr("data-outcomename"):
                        m = re.search(r'(\d+/\d+)', btn["data-outcomename"])
                        if m:
                            return m.group(1)
                    return ""

                if len(odds_cells) >= 1:
                    left_odds = extract_price(odds_cells[0])
                if len(odds_cells) >= 2:
                    right_odds = extract_price(odds_cells[1])

            # Append valid pairs
            if left_name and left_odds:
                players.append(left_name); actions.append(section_title); odds.append(left_odds)
            if right_name and right_odds:
                players.append(right_name); actions.append(section_title); odds.append(right_odds)

            i += 2  # advance to next pair

        df = pd.DataFrame({"Player Name": players, "Action": actions, "Odds": odds})
        dataframes[section_title] = df

    return dataframes

# =========================================================
# 3) ARBITRAGE HELPERS (unchanged math; safer parsing)
# =========================================================

def multiply_fractions(fraction1, fraction2):
    try:
        frac1 = Fraction(fraction1)
        frac2 = Fraction(fraction2)
        return frac1 * frac2
    except Exception:
        return None

def fractional_to_decimal(fraction):
    if fraction.upper().startswith("EV"):
        return 2.0
    num, denom = map(int, fraction.split("/"))
    return 1 + (num / denom)

def calculate_arbitrage_roi(stake, odds1, odds2):
    d1 = fractional_to_decimal(odds1)
    d2 = fractional_to_decimal(odds2)
    stake1 = (d2 / (d1 + d2)) * stake
    stake2 = stake - stake1
    payout = stake1 * d1
    total_profit = payout - stake
    roi = (total_profit / stake) * 100
    return roi, stake1, stake2, total_profit

# Parse "Under 0.5 4/6" (or "Under 1.5 EVS")
def parse_under_parts(under_text: str):
    m_num = re.search(r"(\d+(?:\.\d+)?)", under_text)
    m_frac = re.search(r"(\d+/\d+|EVS|Evens|EVENS)", under_text, flags=re.I)
    if not m_num or not m_frac:
        return None, None
    thresh = float(m_num.group(1))
    frac = m_frac.group(1)
    if frac.upper().startswith("EV"):
        frac = "1/1"
    return thresh, frac

# =========================================================
# 4) RUN SCRAPERS
# =========================================================
bet365_dataframes = scrape_bet365(bet365_file_path)
print("Bet365 Data:")
for section_name, df in bet365_dataframes.items():
    print(section_name)
    print(df.head(30))
    print("\n" + "=" * 50 + "\n")

betway_dataframes = scrape_betway(betway_file_path)
print("Betway Data:")
for section_name, df in betway_dataframes.items():
    print(section_name)
    print(df.head(30))
    print("\n" + "-" * 80 + "\n")

# =========================================================
# 5) ARBITRAGE SCAN
#    Strategy: Bet365 "Under X.5" vs Betway "Player To Have N+ Shots(/On Target)"
# =========================================================

# --- Shots On Target ---
if "Player_Shots_On_Target" in bet365_dataframes:
    bet365_player_shots_on_target = bet365_dataframes["Player_Shots_On_Target"]
    for _, row in bet365_player_shots_on_target.iterrows():
        player_name = row['Player']
        under_odds_text = row['Under']
        if not isinstance(under_odds_text, str) or not under_odds_text:
            continue

        thresh, fractional_odds = parse_under_parts(under_odds_text)
        if thresh is None or fractional_odds is None:
            continue

        rounded_up_number = int(np.ceil(thresh))
        target_section = f"Player To Have {rounded_up_number}+ Shots On Target"

        betway_df = betway_dataframes.get(target_section)
        if betway_df is None or betway_df.empty:
            continue

        # exact name match after stripping whitespace
        match = betway_df.loc[betway_df['Player Name'].str.strip() == player_name]
        if match.empty:
            continue

        betway_fractional = match.iloc[0]['Odds']
        product_fraction = multiply_fractions(fractional_odds, betway_fractional)

        if product_fraction and product_fraction > 1:
            roi, stake1, stake2, total_profit = calculate_arbitrage_roi(100, fractional_odds, betway_fractional)
            print(f"ARBITRAGE OPPORTUNITY! - Shots On Target")
            print(f"Player: {player_name}")
            print(f"Bet365 'Under' Odds: {fractional_odds}")
            print(f"Betway Odds: {betway_fractional}")
            print(f"Guaranteed ROI: {roi:.2f}%")
            print(f"Suggested bet on Bet365: £{stake1:.2f}")
            print(f"Suggested bet on Betway: £{stake2:.2f}")
            print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
            print("-" * 40)

# --- Total Shots ---
if "Player_Total_Shots" in bet365_dataframes:
    bet365_player_total_shots = bet365_dataframes["Player_Total_Shots"]
    for _, row in bet365_player_total_shots.iterrows():
        player_name = row['Player']
        under_odds_text = row['Under']
        if not isinstance(under_odds_text, str) or not under_odds_text:
            continue

        thresh, fractional_odds = parse_under_parts(under_odds_text)
        if thresh is None or fractional_odds is None:
            # Optional debug:
            # print(f"Error parsing Under odds for Player: {player_name}, Odds: {under_odds_text}")
            continue

        rounded_up_number = int(np.ceil(thresh))
        target_section = f"Player To Have {rounded_up_number}+ Shots"

        betway_df = betway_dataframes.get(target_section)
        if betway_df is None or betway_df.empty:
            continue

        match = betway_df.loc[betway_df['Player Name'].str.strip() == player_name]
        if match.empty:
            continue

        betway_fractional = match.iloc[0]['Odds']
        product_fraction = multiply_fractions(fractional_odds, betway_fractional)

        if product_fraction and product_fraction > 1:
            roi, stake1, stake2, total_profit = calculate_arbitrage_roi(100, fractional_odds, betway_fractional)
            print(f"ARBITRAGE OPPORTUNITY! - Shots")
            print(f"Player: {player_name}")
            print(f"Bet365 'Under' Odds: {fractional_odds}")
            print(f"Betway Odds: {betway_fractional}")
            print(f"Guaranteed ROI: {roi:.2f}%")
            print(f"Suggested Bet on Bet365: £{stake1:.2f}")
            print(f"Suggested Bet on Betway: £{stake2:.2f}")
            print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
            print("-" * 40)
