"""SVG house template with colorable sections."""


def house_svg(
    body: str = "#d4c5a9",
    roof: str = "#6b4226",
    trim: str = "#ffffff",
    door: str = "#8b0000",
    windows: str = "#87ceeb",
    garage: str = "#a0937e",
    shutters: str = "#3e5f4f",
    width: int = 600,
    height: int = 450,
) -> str:
    """Return an SVG string of a house with colorable sections."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" style="max-width:100%;height:auto;">

  <!-- Roof -->
  <polygon points="50,180 300,40 550,180" fill="{roof}" stroke="#333" stroke-width="2"/>

  <!-- Body -->
  <rect x="80" y="180" width="440" height="230" fill="{body}" stroke="#333" stroke-width="2"/>

  <!-- Trim — horizontal bands -->
  <rect x="80" y="176" width="440" height="8" fill="{trim}"/>
  <rect x="80" y="402" width="440" height="8" fill="{trim}"/>

  <!-- Door -->
  <rect x="260" y="290" width="60" height="120" rx="3" fill="{door}" stroke="#333" stroke-width="2"/>
  <circle cx="310" cy="355" r="4" fill="#c0a000"/>

  <!-- Windows -->
  <rect x="130" y="230" width="70" height="60" rx="3" fill="{windows}" stroke="{trim}" stroke-width="4"/>
  <line x1="165" y1="230" x2="165" y2="290" stroke="{trim}" stroke-width="2"/>
  <line x1="130" y1="260" x2="200" y2="260" stroke="{trim}" stroke-width="2"/>

  <rect x="380" y="230" width="70" height="60" rx="3" fill="{windows}" stroke="{trim}" stroke-width="4"/>
  <line x1="415" y1="230" x2="415" y2="290" stroke="{trim}" stroke-width="2"/>
  <line x1="380" y1="260" x2="450" y2="260" stroke="{trim}" stroke-width="2"/>

  <!-- Shutters -->
  <rect x="114" y="228" width="16" height="64" fill="{shutters}" stroke="#333" stroke-width="1"/>
  <rect x="200" y="228" width="16" height="64" fill="{shutters}" stroke="#333" stroke-width="1"/>
  <rect x="364" y="228" width="16" height="64" fill="{shutters}" stroke="#333" stroke-width="1"/>
  <rect x="450" y="228" width="16" height="64" fill="{shutters}" stroke="#333" stroke-width="1"/>

  <!-- Garage door -->
  <rect x="400" y="330" width="90" height="80" rx="4" fill="{garage}" stroke="#333" stroke-width="2"/>
  <line x1="400" y1="350" x2="490" y2="350" stroke="#333" stroke-width="1"/>
  <line x1="400" y1="370" x2="490" y2="370" stroke="#333" stroke-width="1"/>
  <line x1="400" y1="390" x2="490" y2="390" stroke="#333" stroke-width="1"/>

  <!-- Ground -->
  <rect x="0" y="410" width="{width}" height="40" fill="#5a8f29"/>
</svg>"""


SECTIONS = ["body", "roof", "trim", "door", "windows", "garage", "shutters"]

DEFAULT_COLORS = {
    "body": "#d4c5a9",
    "roof": "#6b4226",
    "trim": "#ffffff",
    "door": "#8b0000",
    "windows": "#87ceeb",
    "garage": "#a0937e",
    "shutters": "#3e5f4f",
}
