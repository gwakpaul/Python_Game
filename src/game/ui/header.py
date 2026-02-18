from __future__ import annotations

import pygame


class Header:
    """
    모든 씬에서 동일한 헤더 레이아웃을 유지하기 위한 공통 렌더러.

    규칙(현재 기준):
    - 타이틀: 상단 중앙 y=78
    - 서브타이틀(선택): 타이틀 아래 중앙 y=112
    - 좌상단 영역: 홈/뒤로 등 버튼은 씬에서 따로 렌더하되, 헤더 공간과 겹치지 않게 유지
    """

    TITLE_Y = 78
    SUBTITLE_Y = 112

    @staticmethod
    def render(
        screen: pygame.Surface,
        title: str,
        subtitle: str | None,
        title_font: pygame.font.Font,
        subtitle_font: pygame.font.Font,
        title_color: tuple[int, int, int] = (235, 235, 235),
        subtitle_color: tuple[int, int, int] = (190, 190, 190),
    ) -> None:
        cx = screen.get_width() // 2

        title_surf = title_font.render(title, True, title_color)
        title_rect = title_surf.get_rect(center=(cx, Header.TITLE_Y))
        screen.blit(title_surf, title_rect)

        if subtitle:
            sub_surf = subtitle_font.render(subtitle, True, subtitle_color)
            sub_rect = sub_surf.get_rect(center=(cx, Header.SUBTITLE_Y))
            screen.blit(sub_surf, sub_rect)
