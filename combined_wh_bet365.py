# bet365_williamhill_scraper.py

import re
import pandas as pd
from bs4 import BeautifulSoup

# ================================
# 0) Local HTML file paths (edit)
# ================================
bet365_file_path     = r"C:\Users\AhmedZ\Downloads\whubre365.html"
williamhill_file_path = r"C:\Users\AhmedZ\Downloads\whubrewh.html"

# =========================================================
# 1) BET365 — exact market titles, card-based DOM (updated)
#    Returns dict with keys:
#      bet365_Player_Shots_On_Target, bet365_Player_Total_Shots,
#      bet365_Player_Fouls_Committed, bet365_Player_Tackles
#    Each DF has columns: ["Player","Over","Under"] and values like
#      "Over 0.5 6/4", "Under 0.5 1/2"
# =========================================================

BET365_EXACT_TITLES = {
    "bet365_Player_Shots_On_Target": "Player Shots On Target Over/Under",
    "bet365_Player_Total_Shots":     "Player Shots Over/Under",
    "bet365_Player_Fouls_Committed": "Player Fouls Over/Under",
    "bet365_Player_Tackles":         "Player Tackles Over/Under",
}

def _b365_title_of(mg):
    t = mg.find("div", class_="gl-MarketGroup_Name")
    if not t:
        t = mg.find("div", class_="cm-MarketGroupWithIconsButton_Text")
    return t.get_text(strip=True) if t else ""

def _b365_extract_names(market_root):
    # Left label column with all player names
    return [
        div.get_text(strip=True)
        for div in market_root.find_all("div", class_="srb-ParticipantLabelWithTeam_Name")
    ]

def _b365_extract_cells(market_root):
    """
    Return ordered list of (handicap, odds) cells for one market card.
    Prefers CenteredStacked (handicap + odds). Falls back to odds-only if needed.
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

def _b365_df_from_card(market_root, label_text: str):
    """
    Build DF with columns: Player | {label_text}
    Example cell: "Over 0.5 10/11" or "Under 1.5 4/5"
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

def scrape_bet365(file_path: str) -> dict:
    """
    For each exact market title T, look for cards titled exactly:
      - T
      - T - Over
      - T - Under
    If only a combined card T exists, split its cells into Over/Under halves
    by the number of names.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    market_groups = soup.find_all("div", class_="gl-MarketGroup")
    out = {}

    for out_key, exact_title in BET365_EXACT_TITLES.items():
        over_df = under_df = combined_df = None

        # Find cards for this market family
        for mg in market_groups:
            title = _b365_title_of(mg)
            if title == exact_title + " - Over":
                over_df = _b365_df_from_card(mg, "Over")
            elif title == exact_title + " - Under":
                under_df = _b365_df_from_card(mg, "Under")
            elif title == exact_title:
                # Combined O/U card
                combined_df = _b365_df_from_card(mg, "Over_Under_RAW")

            if over_df is not None and under_df is not None:
                break

        # If we only found a combined card, split cells by names length
        if over_df is None and under_df is None and combined_df is not None:
            names = combined_df["Player"].tolist()
            mg_combined = next((mg for mg in market_groups if _b365_title_of(mg) == exact_title), None)
            if mg_combined:
                cells = _b365_extract_cells(mg_combined)
                N = len(names)
                if N and len(cells) >= 2 * N:
                    over_cells  = cells[:N]
                    under_cells = cells[N:2*N]
                    over_df = pd.DataFrame({
                        "Player": names,
                        "Over":  [f"Over {h} {o}".strip()  for (h, o) in over_cells]
                    })
                    under_df = pd.DataFrame({
                        "Player": names,
                        "Under": [f"Under {h} {o}".strip() for (h, o) in under_cells]
                    })

        # Merge Over + Under (or keep whichever exists)
        if over_df is not None and under_df is not None:
            merged = pd.merge(over_df, under_df, on="Player", how="inner")
        elif over_df is not None:
            merged = over_df.copy(); merged["Under"] = ""
        elif under_df is not None:
            merged = under_df.copy(); merged["Over"]  = ""
        else:
            merged = pd.DataFrame(columns=["Player","Over","Under"])

        out[out_key] = merged[["Player","Over","Under"]]

    return out

# =========================================================
# 2) WILLIAM HILL — parse saved HTML (no Selenium)
#    Returns dict with keys:
#      wh_Player_Shots_On_Target, wh_Player_Total_Shots,
#      wh_Player_Fouls_Committed, wh_Player_Tackles
#    Each DF has columns: ["Player Name","Action","Odds"]
# =========================================================

def _wh_find_market_wrapper(soup: BeautifulSoup, market_h2_text: str):
    """
    Locate market by its exact <h2> title and return the wrapper that holds
    all .btmarket__selection rows for that market.
    """
    h2 = soup.find('h2', string=market_h2_text)
    if not h2:
        return None
    header = h2.find_parent('header') or h2.parent
    container = header.find_next_sibling() if header else None
    if not container:
        return None
    return container.find('div', class_='btmarket__wrapper')

def _wh_rows_from_wrapper(wrapper, section_kind: str):
    """
    Extract player rows from a WH market wrapper.
    section_kind ∈ {"SOT","SHOTS","FOULS","TACKLES"}.
    Normalizes "At Least n" → "n+" and "Over n" → "(n+1)+"
    and builds a user-friendly Action label.
    """
    rows = []
    for sel in wrapper.select('div.btmarket__selection'):
        name_p = sel.find('p', class_='btmarket__name')
        if not name_p:
            continue
        raw = name_p.get_text(strip=True)

        # Odds: prefer button's data-odds; fallback to visible text
        btn = sel.find('button')
        odds = btn.get('data-odds', '') if btn else ''
        if not odds:
            span = sel.find('span', class_='betbutton__odds')
            odds = span.get_text(strip=True) if span else ''

        # Examples:
        #   "Callum Wilson Over 2 Shots"
        #   "James Ward-Prowse At Least 1 Shot On Target"
        m = re.match(r'^(?P<player>.+?)\s+(?P<qual>(?:At Least|Over)\s+\d+\s+.*)$', raw)
        if not m:
            continue
        player = m.group('player').strip()
        qual   = m.group('qual').strip()

        num_m = re.search(r'(\d+)', qual)
        if not num_m:
            continue
        n = int(num_m.group(1))
        k = n if qual.startswith("At Least") else n + 1

        if section_kind == "SOT":
            action = f"{k}+ Shots On Target"
        elif section_kind == "SHOTS":
            action = f"{k}+ Shots"
        elif section_kind == "FOULS":
            action = f"{k}+ Fouls"
        elif section_kind == "TACKLES":
            action = f"{k}+ Tackles"
        else:
            action = qual

        rows.append({"Player Name": player, "Action": action, "Odds": odds})

    return pd.DataFrame(rows, columns=["Player Name", "Action", "Odds"])

def scrape_william_hill_html(file_path: str) -> dict:
    """
    Scrapes the four exact markets from a saved WH HTML file.
    **Use the exact <h2> titles present in your file.**
    If WH rename them, just update TARGETS accordingly.
    """
    # Adjust these 4 strings to whatever your page shows exactly:
    TARGETS = [
        ("Player Shots on Target", "SOT"),   # exact case/spacing from your file
        ("Player Fouls",           "FOULS"),
        ("Total Player Shots",     "SHOTS"),
        ("Total Player Tackles",   "TACKLES"),
    ]

    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    key_map = {
        "SOT": "wh_Player_Shots_On_Target",
        "FOULS": "wh_Player_Fouls_Committed",
        "SHOTS": "wh_Player_Total_Shots",
        "TACKLES": "wh_Player_Tackles",
    }

    out = {}
    for title, kind in TARGETS:
        wrapper = _wh_find_market_wrapper(soup, title)
        if not wrapper:
            continue
        df = _wh_rows_from_wrapper(wrapper, kind)
        if df.empty:
            continue
        out[key_map[kind]] = df

    return out

# =================
# 3) Run & preview
# =================
if __name__ == "__main__":
    # Bet365
    b365 = scrape_bet365(bet365_file_path)
    print("\n=== Bet365 DataFrames ===\n")
    for name, df in b365.items():
        print(name)
        print(df.head(30))
        print("\n" + "="*60 + "\n")

    # William Hill
    wh = scrape_william_hill_html(williamhill_file_path)
    print("\n=== William Hill DataFrames ===\n")
    for name, df in wh.items():
        print(name)
        print(df.head(30))
        print("\n" + "="*60 + "\n")
