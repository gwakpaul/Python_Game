from __future__ import annotations


class Stage:
    """
    모든 스테이지(기믹)의 공통 베이스.

    공통 규칙:
    - target(목표값)은 항상 존재
    - current(현재값)은 숫자로 표현 가능한 스테이지만 제공
    - 클리어 판정은 스테이지별로 2가지 모드:
      1) hold: 목표 상태를 hold_seconds 동안 유지하면 자동 클리어
      2) submit: Enter 제출 시점에 목표 상태면 클리어
    """

    def __init__(self, target: int, hold_seconds: float = 0.8, clear_mode: str = "hold") -> None:
        self._target = int(target)
        self._cleared = False

        self._clear_mode = clear_mode  # "hold" or "submit"
        self._hold_seconds = float(hold_seconds)
        self._match_timer = 0.0

    def get_target_value(self) -> int:
        return self._target

    def supports_numeric_value(self) -> bool:
        return False

    def get_current_value(self) -> int:
        raise NotImplementedError

    def get_progress_text(self) -> str | None:
        return None

    def is_cleared(self) -> bool:
        return self._cleared

    def clear_mode(self) -> str:
        return self._clear_mode

    def required_hold_seconds(self) -> float:
        return self._hold_seconds

    def is_matching_target(self) -> bool:
        """
        기본 판정: current == target
        숫자 current가 없는 스테이지는 override로 정의 가능.
        """
        if not self.supports_numeric_value():
            return False
        return int(self.get_current_value()) == int(self.get_target_value())

    def evaluate_hold_clear(self, dt: float) -> None:
        """
        clear_mode == "hold"인 스테이지에서 매 프레임 호출되면,
        목표 상태 유지 시간 누적 후 자동 클리어한다.
        """
        if self._cleared:
            return
        if self._clear_mode != "hold":
            return

        if self.is_matching_target():
            self._match_timer += dt
            if self._match_timer >= self._hold_seconds:
                self._cleared = True
        else:
            self._match_timer = 0.0

    def submit(self) -> bool:
        """
        clear_mode == "submit" 인 스테이지에서 Enter(제출) 시 호출.
        제출 시점에 목표 상태면 클리어.
        """
        if self._cleared:
            return True
        if self._clear_mode != "submit":
            return False
        if self.is_matching_target():
            self._cleared = True
            return True
        return False

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        # 기본은 hold 모드면 자동 판정이 되도록 해둔다.
        self.evaluate_hold_clear(dt)

    def render(self, screen) -> None:
        pass
