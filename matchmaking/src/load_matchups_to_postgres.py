import os
import re
from contextlib import closing
from pathlib import Path

import psycopg

import pipeline_db
from matchmaking.src.env_utils import load_project_env


load_project_env(Path(__file__).resolve())
MATCHUP_COLUMNS = [
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


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return database_url


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower())
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def build_fighter_slug(name: str, weight_class: str, existing: set[str]) -> str:
    base_slug = slugify(name) or "fighter"
    if base_slug not in existing:
        existing.add(base_slug)
        return base_slug

    fallback = f"{base_slug}-{slugify(weight_class) or 'division'}"
    if fallback not in existing:
        existing.add(fallback)
        return fallback

    counter = 2
    while True:
        candidate = f"{fallback}-{counter}"
        if candidate not in existing:
            existing.add(candidate)
            return candidate
        counter += 1


def read_matchup_rows(conn) -> list[dict]:
    # rowid order = the order matchmaking generated the rows. Slug assignment
    # depends on it (the first fighter seen gets the bare slug).
    cursor = conn.execute(
        f"SELECT {', '.join(MATCHUP_COLUMNS)} FROM potential_matchups ORDER BY rowid"
    )
    rows = [dict(zip(MATCHUP_COLUMNS, row)) for row in cursor.fetchall()]

    if not rows:
        raise RuntimeError("potential_matchups table is empty. Run matchmaking first.")

    return rows


def build_slug_maps(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    slug_to_name: dict[str, str] = {}
    name_to_slug: dict[str, str] = {}
    used_slugs: set[str] = set()

    for row in rows:
        fighter_name = row["fighter_name"].strip()
        if fighter_name not in name_to_slug:
            fighter_slug = build_fighter_slug(
                fighter_name,
                row["weight_class"],
                used_slugs,
            )
            name_to_slug[fighter_name] = fighter_slug
            slug_to_name[fighter_slug] = fighter_name

        opponent_name = row["opponent_name"].strip()
        if opponent_name and opponent_name not in name_to_slug:
            opponent_slug = build_fighter_slug(
                opponent_name,
                row["weight_class"],
                used_slugs,
            )
            name_to_slug[opponent_name] = opponent_slug
            slug_to_name[opponent_slug] = opponent_name

    return slug_to_name, name_to_slug


def build_insert_rows(rows: list[dict[str, str]]) -> list[tuple]:
    _, name_to_slug = build_slug_maps(rows)

    return [
        (
            row["fighter_name"].strip(),
            name_to_slug[row["fighter_name"].strip()],
            row["weight_class"].strip(),
            float(row["fighter_rating"]),
            int(float(row["fighter_rank_in_class"])),
            row["last_result_bucket"].strip(),
            int(float(row["slot_number"])),
            row["target_direction"].strip(),
            row["opponent_name"].strip(),
            name_to_slug[row["opponent_name"].strip()],
            float(row["opponent_rating"]),
            int(float(row["opponent_rank_in_class"])),
        )
        for row in rows
    ]


def ensure_schema(cursor: psycopg.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS potential_matchups (
            fighter_name TEXT NOT NULL,
            fighter_slug TEXT NOT NULL,
            weight_class TEXT NOT NULL,
            fighter_rating DOUBLE PRECISION NOT NULL,
            fighter_rank_in_class INTEGER NOT NULL,
            last_result_bucket TEXT NOT NULL,
            slot_number INTEGER NOT NULL,
            target_direction TEXT NOT NULL,
            opponent_name TEXT NOT NULL,
            opponent_slug TEXT NOT NULL,
            opponent_rating DOUBLE PRECISION NOT NULL,
            opponent_rank_in_class INTEGER NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_matchups_fighter_slug
        ON potential_matchups (fighter_slug)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_matchups_fighter_name
        ON potential_matchups (fighter_name)
        """
    )


def load_matchups_to_postgres(conn) -> int:
    rows = read_matchup_rows(conn)
    insert_rows = build_insert_rows(rows)

    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            ensure_schema(cursor)
            cursor.execute("TRUNCATE TABLE potential_matchups")
            cursor.executemany(
                """
                INSERT INTO potential_matchups (
                    fighter_name,
                    fighter_slug,
                    weight_class,
                    fighter_rating,
                    fighter_rank_in_class,
                    last_result_bucket,
                    slot_number,
                    target_direction,
                    opponent_name,
                    opponent_slug,
                    opponent_rating,
                    opponent_rank_in_class
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                insert_rows,
            )

    return len(insert_rows)


def main() -> None:
    with closing(pipeline_db.connect()) as connection:
        inserted_count = load_matchups_to_postgres(connection)
    print(f"Loaded {inserted_count} matchup rows into Postgres from SQLite")


if __name__ == "__main__":
    main()
