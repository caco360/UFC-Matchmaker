import pytest

import pipeline

STAGES = ["scrape", "score", "generate_matchups", "load_matchups_to_postgres"]


def patch_stages(monkeypatch, calls, fail_on=None):
    def make_stage(name):
        def stage(conn):
            calls.append(name)
            if name == fail_on:
                raise RuntimeError(f"{name} failed")
            return 0

        return stage

    for name in STAGES:
        monkeypatch.setattr(pipeline, name, make_stage(name))


def test_default_run_does_not_publish(tmp_path, monkeypatch):
    calls = []
    patch_stages(monkeypatch, calls)

    pipeline.run(db_path=tmp_path / "test.sqlite")

    assert calls == ["scrape", "score", "generate_matchups"]


def test_publish_runs_last_when_requested(tmp_path, monkeypatch):
    calls = []
    patch_stages(monkeypatch, calls)

    pipeline.run(publish=True, db_path=tmp_path / "test.sqlite")

    assert calls == STAGES


def test_failing_stage_stops_the_run(tmp_path, monkeypatch):
    calls = []
    patch_stages(monkeypatch, calls, fail_on="score")

    with pytest.raises(RuntimeError, match="score failed"):
        pipeline.run(publish=True, db_path=tmp_path / "test.sqlite")

    assert calls == ["scrape", "score"]


def test_publish_flag_parsing():
    assert pipeline.parse_args([]).publish is False
    assert pipeline.parse_args(["--publish"]).publish is True
