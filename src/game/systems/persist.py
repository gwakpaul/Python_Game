from __future__ import annotations

import json
from pathlib import Path


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_PROGRESS_PATH = _DATA_DIR / "progress.json"
_SETTINGS_PATH = _DATA_DIR / "settings.json"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: dict) -> dict:
    _ensure_data_dir()
    if not path.exists():
        return dict(default)
    try:
        # Windows에서 BOM이 붙는 경우가 있어 utf-8-sig 사용
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        # 깨졌을 때 기본값으로 복구(크래시 방지)
        return dict(default)


def _save_json(path: Path, data: dict) -> None:
    _ensure_data_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_progress() -> dict:
    return _load_json(_PROGRESS_PATH, {"highest_unlocked": 1})


def save_progress(progress: dict) -> None:
    _save_json(_PROGRESS_PATH, progress)


def load_settings() -> dict:
    """
    master_volume: 0~100 (게임 내부 볼륨)
    """
    s = _load_json(_SETTINGS_PATH, {"master_volume": 50})
    # 안전하게 클램프
    try:
        v = int(s.get("master_volume", 50))
    except Exception:
        v = 50
    v = max(0, min(100, v))
    s["master_volume"] = v
    return s


def save_settings(settings: dict) -> None:
    # 안전하게 클램프
    try:
        v = int(settings.get("master_volume", 50))
    except Exception:
        v = 50
    v = max(0, min(100, v))
    settings = dict(settings)
    settings["master_volume"] = v
    _save_json(_SETTINGS_PATH, settings)
