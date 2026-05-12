from __future__ import annotations

import run_backend


def test_desktop_backend_launcher_runs_local_api_without_browser(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(app: str, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(run_backend.uvicorn, "run", fake_run)

    run_backend.main(["--port", "9001"])

    assert calls == [
        {
            "app": "backend.app.main:app",
            "host": "127.0.0.1",
            "port": 9001,
            "log_level": "warning",
        }
    ]
