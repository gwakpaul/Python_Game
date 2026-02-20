from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


_CATALOG_PATH = Path(__file__).resolve().parents[1] / 'data' / 'stage_catalog.json'


@dataclass(frozen=True)
class StageBalance:
    min_target_distance: int
    hold_seconds: float
    clear_mode: str
    time_limit_seconds: float  # 0이면 제한 없음


class StageCatalog:
    def __init__(self, raw: dict) -> None:
        self._raw = raw
        self._stages = raw.get('stages', [])

        self._num_to_id: dict[int, str] = {}
        for i, s in enumerate(self._stages):
            self._num_to_id[i + 1] = str(s.get('id', ''))

    @staticmethod
    def load() -> 'StageCatalog':
        with open(_CATALOG_PATH, 'r', encoding='utf-8-sig') as f:
            raw = json.load(f)
        return StageCatalog(raw)

    def get_stage_id_by_number(self, n: int) -> str | None:
        return self._num_to_id.get(n)

    def get_balance(self, stage_id: str) -> StageBalance:
        default = StageBalance(
            min_target_distance=30,
            hold_seconds=0.3,
            clear_mode='hold',
            time_limit_seconds=30,
        )

        found = None
        for s in self._stages:
            if str(s.get('id', '')) == stage_id:
                found = s
                break
        if found is None:
            return default

        min_dist = int(found.get('min_target_distance', default.min_target_distance))
        hold_seconds = float(found.get('hold_seconds', default.hold_seconds))
        clear_mode = str(found.get('clear_mode', default.clear_mode))
        time_limit = float(found.get('time_limit_seconds', default.time_limit_seconds))

        if time_limit < 0:
            time_limit = 0

        return StageBalance(
            min_target_distance=min_dist,
            hold_seconds=hold_seconds,
            clear_mode=clear_mode,
            time_limit_seconds=time_limit,
        )
