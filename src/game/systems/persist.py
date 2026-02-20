from __future__ import annotations

import json
from pathlib import Path


# src/game/systems/persist.py
# repo_root = parents[3] = <repo>
_REPO_ROOT = Path(__file__).resolve().parents[3]

# 기본값 템플릿은 src/game/data 에 둔다 (레포에 포함되는 기본 값)
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"  # <repo>/src/game/data
_DEFAULT_PROGRESS_PATH = _DEFAULT_DATA_DIR / "progress.json"
_DEFAULT_SETTINGS_PATH = _DEFAULT_DATA_DIR / "settings.json"

# 실제 유저 저장은 <repo>/save 로 분리한다 (레포에 커밋 대상이 아님)
_SAVE_DIR = _REPO_ROOT / "save"
_SAVE_PROGRESS_PATH = _SAVE_DIR / "progress.json"
_SAVE_SETTINGS_PATH = _SAVE_DIR / "settings.json"


def _ensure_save_dir() -> None:
    _SAVE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _load_json_chain(paths: list[Path], default: dict) -> dict:
    for p in paths:
        data = _read_json(p)
        if isinstance(data, dict):
            return data
    return dict(default)


def _save_json(path: Path, data: dict) -> None:
    _ensure_save_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


def load_progress() -> dict:
    return _load_json_chain(
        paths=[_SAVE_PROGRESS_PATH, _DEFAULT_PROGRESS_PATH],
        default={"highest_unlocked": 1},
    )


def save_progress(progress: dict) -> None:
    _save_json(_SAVE_PROGRESS_PATH, dict(progress))


def load_settings() -> dict:
    s = _load_json_chain(
        paths=[_SAVE_SETTINGS_PATH, _DEFAULT_SETTINGS_PATH],
        default={"master_volume": 50, "output_gain": 100},
    )

    try:
        v = int(s.get("master_volume", 50))
    except Exception:
        v = 50
    s["master_volume"] = _clamp_int(v, 0, 100)

    try:
        g = int(s.get("output_gain", 100))
    except Exception:
        g = 100
    s["output_gain"] = _clamp_int(g, 0, 100)

    return s


def save_settings(settings: dict) -> None:
    settings = dict(settings)

    try:
        v = int(settings.get("master_volume", 50))
    except Exception:
        v = 50
    settings["master_volume"] = _clamp_int(v, 0, 100)

    try:
        g = int(settings.get("output_gain", 100))
    except Exception:
        g = 100
    settings["output_gain"] = _clamp_int(g, 0, 100)

    _save_json(_SAVE_SETTINGS_PATH, settings)
