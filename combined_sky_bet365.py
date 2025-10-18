# football_arbitrage_scraper.py

import re
import math
import pandas as pd
from bs4 import BeautifulSoup

# =========================================================
# 1) CONFIG: set these to your saved HTML files
# =========================================================
bet365_file_path = r"C:\Users\AhmedZ\Downloads\whubre365.html"
skybet_file_path = r"C:\Users\AhmedZ\Downloads\whubresky.html"

# =========================================================
# 2) SKY BET — exact titles
# =========================================================

SKYBET_MARKETS = {
    "Player Shots On Target": "Player_Shots_On_Target",
    "Player Total Shots": "Player_Total_Shots",
    "Player Fouls Committed": "Player_Fouls_Committed",
    "Player Tackles": "Player_Tackles",
}

def _class_endswith(suffix):
    return lambda c: isinstance(c, str) and c.endswith(suffix)

def _sky_find_market_card(soup, exact_title):
    # Exact text match
    h3 = soup.find("h3", string=exact_title)
    if not h3:
        return None
    return h3.find_parent(class_=_class_endswith("-card")) or h3.parent

def _sky_parse_runner_lines(card):
    """
    Each player row has a name (-runnerName) and a series of buttons (-label with fractional odds).
    Thresholds are inferred by column index: 1+, 2+, 3+, ...
    """
    out = []
    for row in card.find_all(class_=_class_endswith("-gridRunnerLine")):
        name_tag = row.find(class_=_class_endswith("-runnerName"))
        if not name_tag:
            continue
        player = name_tag.get_text(strip=True)

        odds = []
        for btn in row.find_all("button"):
            label = btn.find(class_=_class_endswith("-label"))
            if label:
                text = label.get_text(strip=True)
                if re.fullmatch(r"\d+/\d+", text):
                    odds.append(text)

        for i, frac in enumerate(odds, start=1):
            out.append({"Player Name": player, "Action": f"{i}+", "Odds": frac})

    return pd.DataFrame(out, columns=["Player Name", "Action", "Odds"]) if out else pd.DataFrame(columns=["Player Name","Action","Odds"])

def scrape_skybet(path: str):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    dataframes = {}
    for exact_title, key in SKYBET_MARKETS.items():
        card = _sky_find_market_card(soup, exact_title)
        if not card:
            continue
        df = _sky_parse_runner_lines(card)
        if key == "Player_Fouls_Committed" and not df.empty:
            df["Player Name"] = df["Player Name"].str.replace(" To Commit", "", regex=False)
        dataframes[key] = df

    return {f"sky_{k}": v for k, v in dataframes.items()}

# =========================================================
# 3) BET365 — exact titles
# =========================================================

# Exact market titles as shown on the page right now
BET365_EXACT_TITLES = {
    "bet365_Player_Shots_On_Target": "Player Shots On Target Over/Under",
    "bet365_Player_Total_Shots":     "Player Shots Over/Under",
    "bet365_Player_Fouls_Committed": "Player Fouls Over/Under",
    "bet365_Player_Tackles":         "Player Tackles Over/Under",
}

_FRACT_RE = re.compile(r"(?:\d+/\d+|EVS|Evens|EVENS)", re.I)

def _norm_frac(s: str) -> str:
    s = s.strip().upper()
    return "1/1" if s in {"EVS", "EVENS"} else s.lower()

def _title_of(mg):
    # Titles appear in one of these nodes; we read exact text
    t = mg.find("div", class_="gl-MarketGroup_Name")
    if not t:
        t = mg.find("div", class_="cm-MarketGroupWithIconsButton_Text")
    return t.get_text(strip=True) if t else ""

def _b365_extract_names(market_root):
    # Player labels in this grid
    return [div.get_text(strip=True)
            for div in market_root.find_all("div", class_="srb-ParticipantLabelWithTeam_Name")]

def _b365_extract_cells(market_root):
    """
    Return ordered list of (handicap, odds) cells.
    Prefer CenteredStacked (handicap + odds); fallback to odds-only spans if needed.
    """
    cells = []
    for cell in market_root.find_all("div", class_="gl-ParticipantCenteredStacked"):
        h = cell.find("span", class_="gl-ParticipantCenteredStacked_Handicap")
        o = cell.find("span", class_="gl-ParticipantCenteredStacked_Odds")
        if h and o:
            hc = h.get_text(strip=True)
            ov = o.get_text(strip=True)
            cells.append((hc, ov))
    if not cells:
        for oo in market_root.find_all("span", class_="gl-ParticipantOddsOnly_Odds"):
            cells.append(("", oo.get_text(strip=True)))
    return cells

def _b365_extract_market_df(market_root, label_text: str):
    """
    Build DataFrame with columns: Player | {label_text}
    row value example: "Over 0.5 10/11"
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

def scrape_bet365(path: str):
    """
    For each exact market title T, look for cards whose title is exactly:
      - T
      - T + " - Over"
      - T + " - Under"
    If only a combined card T is found, split the cells into two halves by name count.
    """
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    market_groups = soup.find_all("div", class_="gl-MarketGroup")
    out = {}

    for out_key, exact_title in BET365_EXACT_TITLES.items():
        over_df = under_df = combined_df = None

        for mg in market_groups:
            title = _title_of(mg)

            if title == exact_title + " - Over":
                over_df = _b365_extract_market_df(mg, "Over")
            elif title == exact_title + " - Under":
                under_df = _b365_extract_market_df(mg, "Under")
            elif title == exact_title:
                # Save combined to potentially split later
                combined_df = _b365_extract_market_df(mg, "Over_Under_RAW")

            if over_df is not None and under_df is not None:
                break

        if over_df is None and under_df is None and combined_df is not None:
            # Split combined card into Over/Under halves by the number of names
            names = combined_df["Player"].tolist()
            # Re-extract cells to know how many items we have
            # (Use the same market group again — find it by exact title)
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

        out[out_key] = merged[["Player", "Over", "Under"]]

    return out

# =========================================================
# 4) ARBITRAGE UTILS + SCAN (unchanged)
# =========================================================

def fractional_to_decimal(frac: str) -> float:
    if not frac:
        return None
    s = frac.upper()
    if s in {"EVS", "EVENS"}:
        return 2.0
    if "/" in frac:
        num, den = frac.split("/")
        return 1 + (int(num) / int(den))
    return None

def calculate_arbitrage_roi(stake, odds1, odds2):
    d1 = fractional_to_decimal(odds1)
    d2 = fractional_to_decimal(odds2)
    if not d1 or not d2:
        return None, None, None, None
    stake1 = (d2 / (d1 + d2)) * stake
    stake2 = stake - stake1
    payout = stake1 * d1
    total_profit = payout - stake
    roi = (total_profit / stake) * 100
    return roi, stake1, stake2, total_profit

# =========================================================
# 5) RUN
# =========================================================

if __name__ == "__main__":
    bet365_dataframes_renamed = scrape_bet365(bet365_file_path)
    skybet_dataframes_renamed = scrape_skybet(skybet_file_path)

    for section_name, df in bet365_dataframes_renamed.items():
        print(f"{section_name}:")
        print(df.head(15))
        print("\n" + "="*60 + "\n")

    for section_name, df in skybet_dataframes_renamed.items():
        print(f"{section_name}:")
        print(df.head(15))
        print("\n" + "="*60 + "\n")

    # Compare for arbitrage
    dataframes_to_process = [
        ("Player_Shots_On_Target", "Shots On Target"),
        ("Player_Total_Shots", "Total Shots"),
        ("Player_Fouls_Committed", "Fouls Committed"),
        ("Player_Tackles", "Tackles"),
    ]

    for dataframe_key, description in dataframes_to_process:
        bkey = f"bet365_{dataframe_key}"
        skey = f"sky_{dataframe_key}"
        if bkey not in bet365_dataframes_renamed or skey not in skybet_dataframes_renamed:
            continue

        bet365_df = bet365_dataframes_renamed[bkey].copy()
        skybet_df = skybet_dataframes_renamed[skey].copy()
        if bet365_df.empty or skybet_df.empty:
            continue

        bet365_df["__name_lc"] = bet365_df["Player"].str.lower().str.strip()
        skybet_df["__name_lc"] = skybet_df["Player Name"].str.lower().str.strip()

        for _, row in bet365_df.iterrows():
            player_name = row["Player"]
            under_text = str(row.get("Under", ""))

            m = re.search(r"(\d+(?:\.\d+)?)", under_text)
            if not m:
                continue
            threshold = float(m.group(1))
            rounded = int(math.ceil(threshold))  # 0.5 -> 1, 1.5 -> 2, etc.

            sky_matches = skybet_df.loc[
                (skybet_df["__name_lc"] == player_name.lower()) &
                (skybet_df["Action"].str.contains(rf"\b{rounded}\+", case=False, na=False))
            ]
            if sky_matches.empty:
                continue

            mfrac = re.search(r"(\d+/\d+|EVS|Evens|EVENS)", under_text, flags=re.I)
            if not mfrac:
                continue
            bet365_fractional_odds = mfrac.group(1)
            if bet365_fractional_odds.upper().startswith("EV"):
                bet365_fractional_odds = "1/1"

            skybet_fractional_odds = sky_matches.iloc[0]["Odds"]

            roi, stake1, stake2, total_profit = calculate_arbitrage_roi(100, bet365_fractional_odds, skybet_fractional_odds)
            if roi is not None and roi > 0:
                print(f"ARBITRAGE OPPORTUNITY - {description}")
                print(f"Player: {player_name}")
                print(f"Bet365 'Under' Odds: {bet365_fractional_odds}")
                print(f"SkyBet Odds: {skybet_fractional_odds}")
                print(f"Guaranteed ROI: {roi:.2f}%")
                print(f"Suggested Bet on Bet365: £{stake1:.2f}")
                print(f"Suggested Bet on SkyBet: £{stake2:.2f}")
                print(f"Total Profit with £100 wallet: £{total_profit:.2f}")
                print("-" * 50)
