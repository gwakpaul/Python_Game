from __future__ import annotations

from typing import Callable, Type

from .stage_base import Stage


class StageRegistry:
    """
    stage_id -> Stage 클래스 매핑.
    스테이지 추가 시 여기 등록만 하면 된다.
    """

    def __init__(self) -> None:
        self._map: dict[str, Type[Stage]] = {}

    def register(self, stage_cls: Type[Stage]) -> None:
        self._map[stage_cls.stage_id] = stage_cls

    def create(self, stage_id: str, target: int) -> Stage:
        if stage_id not in self._map:
            raise KeyError(f"Unknown stage_id: {stage_id}")
        return self._map[stage_id](target)
