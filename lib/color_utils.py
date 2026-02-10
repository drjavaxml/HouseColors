"""Color conversion and distance utilities."""

import math


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """'#RRGGBB' -> (R, G, B)."""
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """(R, G, B) -> '#RRGGBB'."""
    return f"#{r:02x}{g:02x}{b:02x}"


def color_distance(c1: tuple, c2: tuple) -> float:
    """Euclidean distance in RGB space."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def complementary(hex_str: str) -> str:
    """Return the complementary color."""
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(255 - r, 255 - g, 255 - b)


def analogous(hex_str: str, shift: int = 30) -> list[str]:
    """Return two analogous colors by hue-shifting in a simple way."""
    r, g, b = hex_to_rgb(hex_str)
    # Rotate channels as a rough hue shift
    colors = []
    for s in (shift, -shift):
        nr = max(0, min(255, r + s))
        ng = max(0, min(255, g - s))
        nb = max(0, min(255, b + s // 2))
        colors.append(rgb_to_hex(nr, ng, nb))
    return colors


def triadic(hex_str: str) -> list[str]:
    """Return two triadic colors by rotating RGB channels."""
    r, g, b = hex_to_rgb(hex_str)
    return [rgb_to_hex(g, b, r), rgb_to_hex(b, r, g)]


def color_swatch_html(hex_str: str, size: int = 30) -> str:
    """Return an HTML span showing a color swatch."""
    return (
        f'<span style="display:inline-block;width:{size}px;height:{size}px;'
        f'background:{hex_str};border:1px solid #888;border-radius:4px;'
        f'vertical-align:middle;margin-right:6px;"></span>'
    )
