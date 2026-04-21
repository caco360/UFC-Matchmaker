import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
try:
    from .env_utils import load_project_env
except ImportError:
    from env_utils import load_project_env


load_project_env(Path(__file__).resolve())


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_database_url(), row_factory=dict_row)


def search_fighters(query: str, limit: int = 8) -> list[dict]:
    normalized = query.strip()
    if not normalized:
        return []

    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                slug,
                fighter_name,
                weight_class,
                fighter_rank_in_class,
                fighter_rating,
                last_result_bucket
            FROM (
                SELECT DISTINCT ON (fighter_slug)
                    fighter_slug AS slug,
                    fighter_name,
                    weight_class,
                    fighter_rank_in_class,
                    fighter_rating,
                    last_result_bucket,
                    slot_number
                FROM potential_matchups
                WHERE fighter_name ILIKE %s
                ORDER BY fighter_slug, slot_number ASC
            ) fighters
            ORDER BY fighter_rank_in_class ASC, fighter_name ASC
            LIMIT %s
            """,
            (f"%{normalized}%", limit),
        )
        return cursor.fetchall()


def get_fighter(slug: str) -> dict | None:
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                fighter_slug AS slug,
                fighter_name,
                weight_class,
                fighter_rank_in_class,
                fighter_rating,
                last_result_bucket
            FROM potential_matchups
            WHERE fighter_slug = %s
            ORDER BY slot_number ASC
            LIMIT 1
            """,
            (slug,),
        )
        return cursor.fetchone()


def get_matchups(slug: str) -> list[dict]:
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                slot_number,
                target_direction,
                opponent_slug,
                opponent_name,
                opponent_rating,
                opponent_rank_in_class
            FROM potential_matchups
            WHERE fighter_slug = %s
            ORDER BY slot_number ASC
            """,
            (slug,),
        )
        return cursor.fetchall()
