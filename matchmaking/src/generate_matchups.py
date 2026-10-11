from contextlib import closing

import pandas as pd

import pipeline_db


OUTPUT_COLUMNS = [
    "fighter_name",
    "weight_class",
    "fighter_rating",
    "fighter_rank_in_class",
    "last_result_bucket",
    "slot_number",
    "target_direction",
    "opponent_name",
    "opponent_rating",
    "opponent_rank_in_class",
]


def normalize_name(value):
    return str(value).strip()


def normalize_result(value):
    # Same rules as scoring's result normalization, applied to raw scraped values.
    result = str(value).strip().lower()
    if "draw" in result:
        return "draw"
    if "nc" in result or "no contest" in result:
        return "nc"
    if "win" in result:
        return "win"
    return "unknown"


def fighter_2_result(result):
    if result == "win":
        return "loss"
    if result == "draw":
        return "draw"
    if result == "nc":
        return "nc"
    return "unknown"


def result_bucket(result):
    if result in {"win", "draw"}:
        return "win"
    return "loss"


def load_active_fighters(conn):
    active_fighters = pd.read_sql("SELECT fighter_name FROM active_fighters", conn)

    active_fighters["fighter_name"] = active_fighters["fighter_name"].apply(normalize_name)
    active_fighters = active_fighters[active_fighters["fighter_name"] != ""]
    active_fighters = active_fighters[active_fighters["fighter_name"].str.lower() != "nan"]

    return active_fighters.drop_duplicates("fighter_name").reset_index(drop=True)


def load_fighters_score(conn):
    fighters_score = pd.read_sql(
        "SELECT fighter_name, rating, RD, sigma, weight_class FROM fighter_ratings",
        conn,
    )
    fighters_score["fighter_name"] = fighters_score["fighter_name"].apply(normalize_name)
    fighters_score["weight_class"] = fighters_score["weight_class"].astype(str).str.strip()

    return fighters_score.drop_duplicates("fighter_name").reset_index(drop=True)


def load_fights(conn):
    fights = pd.read_sql(
        """
        SELECT f.fighter_1, f.fighter_2, f.result, e.event_date
        FROM fights f
        JOIN events e ON e.event_id = f.event_id
        ORDER BY e.event_date ASC, e.event_id ASC, f.fight_order DESC
        """,
        conn,
    )
    fights["fighter_1"] = fights["fighter_1"].apply(normalize_name)
    fights["fighter_2"] = fights["fighter_2"].apply(normalize_name)
    fights["result"] = fights["result"].apply(normalize_result)
    fights["event_date_parsed"] = pd.to_datetime(fights["event_date"], errors="coerce")
    fights["_row_order"] = range(len(fights))

    return fights


def derive_latest_result_buckets(fights):
    fighter_1_history = fights[
        ["fighter_1", "result", "event_date_parsed", "_row_order"]
    ].rename(columns={"fighter_1": "fighter_name"})

    fighter_2_history = fights[
        ["fighter_2", "result", "event_date_parsed", "_row_order"]
    ].rename(columns={"fighter_2": "fighter_name"})
    fighter_2_history["result"] = fighter_2_history["result"].apply(fighter_2_result)

    fighter_history = pd.concat([fighter_1_history, fighter_2_history], ignore_index=True)
    fighter_history = fighter_history.sort_values(
        ["fighter_name", "event_date_parsed", "_row_order"],
        ascending=[True, True, True],
    )

    latest_results = fighter_history.groupby("fighter_name", as_index=False).tail(1).copy()
    latest_results["last_result_bucket"] = latest_results["result"].apply(result_bucket)

    return latest_results.set_index("fighter_name")["last_result_bucket"].to_dict()


def build_matchup_rows(active_fighters, latest_result_buckets):
    matchup_rows = []

    for weight_class, class_group in active_fighters.groupby("weight_class", sort=False):
        class_group = class_group.sort_values("rating", ascending=False).reset_index(drop=True)
        class_group["fighter_rank_in_class"] = class_group.index + 1

        class_rows = class_group.to_dict("records")

        for index, fighter in enumerate(class_rows):
            bucket = latest_result_buckets.get(fighter["fighter_name"], "loss")

            above_candidates = list(reversed(class_rows[:index]))
            below_candidates = class_rows[index + 1 :]

            if bucket == "win":
                ordered_candidates = [
                    ("above", above_candidates[:2]),
                    ("below", below_candidates[:1]),
                ]
            else:
                ordered_candidates = [
                    ("below", below_candidates[:2]),
                    ("above", above_candidates[:1]),
                ]

            chosen_matchups = []
            for direction, candidates in ordered_candidates:
                for candidate in candidates:
                    chosen_matchups.append((direction, candidate))

            for slot_number, (direction, opponent) in enumerate(chosen_matchups, start=1):
                matchup_rows.append(
                    {
                        "fighter_name": fighter["fighter_name"],
                        "weight_class": weight_class,
                        "fighter_rating": fighter["rating"],
                        "fighter_rank_in_class": fighter["fighter_rank_in_class"],
                        "last_result_bucket": bucket,
                        "slot_number": slot_number,
                        "target_direction": direction,
                        "opponent_name": opponent["fighter_name"],
                        "opponent_rating": opponent["rating"],
                        "opponent_rank_in_class": opponent["fighter_rank_in_class"],
                    }
                )

    return pd.DataFrame(matchup_rows, columns=OUTPUT_COLUMNS)


def generate_matchups(conn):
    active_fighters = load_active_fighters(conn)
    fighters_score = load_fighters_score(conn)
    fights = load_fights(conn)

    active_names = set(active_fighters["fighter_name"])
    matched_fighters = fighters_score[fighters_score["fighter_name"].isin(active_names)].copy()
    matched_fighters = matched_fighters.sort_values(
        ["weight_class", "rating"],
        ascending=[True, False],
    ).reset_index(drop=True)

    unmatched_active = sorted(active_names - set(matched_fighters["fighter_name"]))
    if unmatched_active:
        print("Active fighters missing from fighter_ratings:")
        for fighter_name in unmatched_active:
            print(f"- {fighter_name}")

    latest_result_buckets = derive_latest_result_buckets(fights)
    potential_matchups = build_matchup_rows(matched_fighters, latest_result_buckets)

    conn.execute("DELETE FROM potential_matchups")
    potential_matchups.to_sql("potential_matchups", conn, if_exists="append", index=False)
    conn.commit()

    print(
        f"matchmake: {len(potential_matchups)} matchup rows, "
        f"{matched_fighters['fighter_name'].nunique()} active fighters with scores"
    )

    return potential_matchups


if __name__ == "__main__":
    with closing(pipeline_db.connect()) as connection:
        generate_matchups(connection)
