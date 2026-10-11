from contextlib import closing
import math

import pandas as pd

import pipeline_db


# Oldest event first; within an event the highest fight_order (first fight on
# the card) first. Same order as the old reversed ufc_fights.csv.
FIGHTS_QUERY = """
SELECT
    f.fight_id,
    e.event_name,
    e.event_date,
    f.fighter_1,
    f.fighter_2,
    f.result,
    f.weight_class,
    f.method,
    f.round
FROM fights f
JOIN events e ON e.event_id = f.event_id
ORDER BY e.event_date ASC, e.event_id ASC, f.fight_order DESC
"""


def load_fights(conn):
    ufc_fights = pd.read_sql(FIGHTS_QUERY, conn)
    if ufc_fights.empty:
        raise RuntimeError("No fights in the database. Run scraping first.")
    return ufc_fights


def normalize_fights(ufc_fights):
    ufc_fights["result"] = ufc_fights["result"].astype(str).str.lower().apply(
        lambda x: "draw"
        if "draw" in x
        else ("nc" if "nc" in x or "no contest" in x else ("win" if "win" in x else "unknown"))
    )

    ufc_fights["method"] = ufc_fights["method"].astype(str).str.upper().apply(
        lambda x: "ko_tko"
        if x.startswith("KO/TKO")
        else ("submission" if x.startswith("SUB") else ("decision" if "DEC" in x else "other"))
    )
    ufc_fights["round"] = pd.to_numeric(ufc_fights["round"], errors="coerce")
    ufc_fights["fighter_1"] = ufc_fights["fighter_1"].astype(str).str.strip()
    ufc_fights["fighter_2"] = ufc_fights["fighter_2"].astype(str).str.strip()
    ufc_fights["weight_class"] = ufc_fights["weight_class"].astype(str).str.strip()
    return ufc_fights


def load_fighters(fighters, name, weight):
    if name not in fighters:
        fighters[name] = {
            "rating": 1500.0,
            "RD": 350.0,
            "sigma": 0.06,
            "weight_class": weight,
        }


def update_sigma(phi, delta, v, sigma, tau):
    # iterative solver here
    return sigma


def update_rating(fighter1, fighter2, result, method, round):
    # fighter1 and 2 dict with rating,rd and sigma
    # result: 1,0,0.5
    adjusted_result = result

    if method in ["ko_tko"]:
        adjusted_result = min(1.0, adjusted_result + 0.1)
    elif method in ["submission"]:
        adjusted_result = min(1.0, adjusted_result + 0.08)
    elif method == "decision":
        adjusted_result = max(0.0, adjusted_result - 0.05)

    # round impact to see later.

    r1, RD1, sigma1 = fighter1["rating"], fighter1["RD"], fighter1["sigma"]
    r2, RD2, sigma2 = fighter2["rating"], fighter2["RD"], fighter2["sigma"]

    def g(phi):
        return 1 / math.sqrt(1 + (3 * phi**2) / (math.pi**2))

    def E(mu, mu_j, phi_j):
        return 1 / (1 + math.exp(-g(phi_j) * (mu - mu_j)))

    # nomralized values for glicko2
    mu1 = (r1 - 1500) / 173.7178
    mu2 = (r2 - 1500) / 173.7178
    phi1 = RD1 / 173.7178
    phi2 = RD2 / 173.7178

    # expected score
    E1 = E(mu1, mu2, phi2)

    # delta and v
    v = 1 / (g(phi2) ** 2 * E1 * (1 - E1))
    delta = v * g(phi2) * (adjusted_result - E1)

    sigma1_new = sigma1
    sigma2_new = sigma2

    phi1_new = 1 / math.sqrt((1 / phi1**2) + (1 / v))
    phi2_new = phi2  # (I would symmetrically update f2 in full version)

    mu1_new = mu1 + phi1_new**2 * g(phi2) * (adjusted_result - E1)
    mu2_new = mu2 + phi2**2 * g(phi1) * ((1 - adjusted_result) - (1 - E1))

    # reverse normalization
    r1_new = 173.7178 * mu1_new + 1500
    r2_new = 173.7178 * mu2_new + 1500

    RD1_new = phi1_new * 173.7178
    RD2_new = phi2 * 173.7178

    return (
        {"rating": r1_new, "RD": RD1_new, "sigma": sigma1_new},
        {"rating": r2_new, "RD": RD2_new, "sigma": sigma2_new},
    )


score_map = {"win": 1.0, "draw": 0.5}


def compute_ratings(ufc_fights):
    fighters = {}
    ufc_fights["fighter_1_rating_start"] = None
    ufc_fights["fighter_2_rating_start"] = None
    ufc_fights["fighter_1_rating_end"] = None
    ufc_fights["fighter_2_rating_end"] = None

    for idx, row in ufc_fights.iterrows():
        fighter1 = row["fighter_1"]
        fighter2 = row["fighter_2"]

        weight = row["weight_class"]

        load_fighters(fighters, fighter1, weight)
        load_fighters(fighters, fighter2, weight)
        if weight != "Catch Weight":
            fighters[fighter1]["weight_class"] = weight
            fighters[fighter2]["weight_class"] = weight

        result_name = row["result"]
        method = row["method"]
        round_ = row["round"]

        ufc_fights.at[idx, "fighter_1_rating_start"] = fighters[fighter1]["rating"]
        ufc_fights.at[idx, "fighter_2_rating_start"] = fighters[fighter2]["rating"]

        if result_name == "nc":
            ufc_fights.at[idx, "fighter_1_rating_end"] = fighters[fighter1]["rating"]
            ufc_fights.at[idx, "fighter_2_rating_end"] = fighters[fighter2]["rating"]
            continue

        result = score_map.get(result_name, 0.5)

        f1, f2 = update_rating(
            fighters[fighter1],
            fighters[fighter2],
            result,
            method,
            round_,
        )
        if weight != "Catch Weight":
            f1["weight_class"] = weight
            f2["weight_class"] = weight
        else:
            f1["weight_class"] = fighters[fighter1]["weight_class"]
            f2["weight_class"] = fighters[fighter2]["weight_class"]
        fighters[fighter1] = f1
        fighters[fighter2] = f2

        ufc_fights.at[idx, "fighter_1_rating_end"] = fighters[fighter1]["rating"]
        ufc_fights.at[idx, "fighter_2_rating_end"] = fighters[fighter2]["rating"]

    fighters_df = (
        pd.DataFrame.from_dict(fighters, orient="index")
        .reset_index()
        .rename(columns={"index": "fighter_name"})
        .sort_values("rating", ascending=False)
        .reset_index(drop=True)
    )
    return ufc_fights, fighters_df


def save_ratings(conn, ufc_fights, fighters_df):
    conn.execute("DELETE FROM fight_ratings")
    conn.execute("DELETE FROM fighter_ratings")
    fighters_df[["fighter_name", "rating", "RD", "sigma", "weight_class"]].to_sql(
        "fighter_ratings", conn, if_exists="append", index=False
    )
    ufc_fights[
        [
            "fight_id",
            "fighter_1_rating_start",
            "fighter_2_rating_start",
            "fighter_1_rating_end",
            "fighter_2_rating_end",
        ]
    ].to_sql("fight_ratings", conn, if_exists="append", index=False)
    conn.commit()


def score(conn):
    ufc_fights = normalize_fights(load_fights(conn))
    ufc_fights, fighters_df = compute_ratings(ufc_fights)
    save_ratings(conn, ufc_fights, fighters_df)

    summary = {"fights": len(ufc_fights), "fighters": len(fighters_df)}
    print(f"score: {summary['fights']} fights scored, {summary['fighters']} fighters rated")
    return summary


if __name__ == "__main__":
    with closing(pipeline_db.connect()) as connection:
        score(connection)
