"""TUI theme and styling."""

from textual.theme import Theme

BLOOMFOLIO_THEME = Theme(
    name="bloomfolio",
    primary="#FFA500",      # Amber/orange
    secondary="#00CED1",    # Cyan
    background="#0D0D0D",   # Near black
    surface="#1A1A1A",      # Dark grey
    panel="#141414",        # Panel background
    success="#00FF7F",      # Green
    warning="#FFA500",      # Amber
    error="#FF4500",        # Red
    accent="#00CED1",       # Cyan accent
    dark=True,
)

# Custom CSS variables
CSS_VARIABLES = """
$amber: #FFA500;
$cyan: #00CED1;
$green: #00FF7F;
$red: #FF4500;
$background: #0D0D0D;
$surface: #1A1A1A;
$panel: #141414;
$text: #E0E0E0;
$text-muted: #808080;
$border: #333333;
"""
