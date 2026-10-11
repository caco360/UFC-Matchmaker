import argparse
from contextlib import closing

import pipeline_db
from matchmaking.src.generate_matchups import generate_matchups
from matchmaking.src.load_matchups_to_postgres import load_matchups_to_postgres
from scoring.src.score_generator import score
from scraping.src.main import scrape


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the UFC matchmaking pipeline.")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Also load the fresh matchups into Postgres/Neon (production).",
    )
    return parser.parse_args(argv)


def run(publish=False, db_path=pipeline_db.DB_PATH):
    # Each stage raises on failure, which stops the run before later stages.
    with closing(pipeline_db.connect(db_path)) as conn:
        scrape(conn)
        score(conn)
        generate_matchups(conn)

        if publish:
            count = load_matchups_to_postgres(conn)
            print(f"publish: {count} matchup rows loaded into Postgres")


def main():
    args = parse_args()
    run(publish=args.publish)


if __name__ == "__main__":
    main()
