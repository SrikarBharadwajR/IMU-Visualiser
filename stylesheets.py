# stylesheets.py
# Contains the CSS-like stylesheets for the application's themes.

# Theme Colors
NEON_BLUE = "#7D7DFF"
NEON_BLUE_HOVER = "#9393FF"
DARK_BACKGROUND = "#1E1E2E"
DARK_FOREGROUND = "#E5E5E5"
LIGHT_BACKGROUND = "#EFF1F5"
LIGHT_FOREGROUND = "#4C4F69"
FONT_FAMILY = "'Segoe UI', 'Arial', 'sans-serif'"
FONT_SIZE = "10pt"

# Status Colors
DARK_GREEN = "#A6E3A1"
DARK_RED = "#F38BA8"
LIGHT_GREEN = "#40A02B"
LIGHT_RED = "#D20F39"


DARK_STYLE = f"""
    QMainWindow {{
        background-color: {DARK_BACKGROUND};
    }}
    QWidget {{
        background-color: {DARK_BACKGROUND};
        color: {DARK_FOREGROUND};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE};
    }}
    QSplitter::handle {{ background: #45475A; }}
    QGroupBox {{
        border: 1px solid #45475A;
        border-radius: 8px;
        margin-top: 0.5em;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 10px;
        background-color: #313244;
        border-radius: 5px;
        color: {NEON_BLUE_HOVER};
        font-weight: bold;
    }}
    
    /* Visualisation Box Style */
    QGroupBox#VisualisationBox {{
        border: 1px solid #45475A;
    }}
     QGroupBox#VisualisationBox::title {{
        subcontrol-position: top left;
        padding-left: 10px;
    }}
    
    /* Status-specific coloring */
    QLabel#infoLabel[status="ok"] {{ color: {DARK_GREEN}; }}
    QLabel#infoLabel[status="error"] {{ color: {DARK_RED}; font-weight: bold; }}
    QLabel#rateLabel {{ color: #000000; }}
    
    QComboBox, QPushButton {{
        min-height: 28px;
    }}
    QComboBox {{
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 5px; padding: 5px;
        min-width: 80px;
    }}
    QComboBox:hover {{ background-color: #45475A; }}

    QPushButton {{
        background-color: {NEON_BLUE};
        color: {DARK_BACKGROUND};
        border: none; border-radius: 5px;
        padding: 6px 12px; font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {NEON_BLUE_HOVER}; }}
    
    QPushButton#themeButton {{
        background-color: transparent;
        border: 1px solid {NEON_BLUE};
        color: {DARK_FOREGROUND};
        font-size: 14pt;
        padding: 2px 8px;
    }}
    QPushButton#themeButton:hover {{ background-color: #45475A; }}

    QPushButton#refreshButton {{
        background-color: {NEON_BLUE};
        border: none;
    }}
    QPushButton#refreshButton:hover {{ background-color: {NEON_BLUE_HOVER}; }}

    /* Disabled Styles */
    QComboBox:disabled, QPushButton:disabled {{
        background-color: #313244;
        color: #6C7086;
        border-color: #45475A;
    }}
    QPushButton#refreshButton:disabled {{ background-color: #313244; }}

    /* Status Box Style (now a QWidget) */
    QWidget#statusBox {{
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 6px;
    }}

"""

LIGHT_STYLE = f"""
    QMainWindow {{
        background-color: {LIGHT_BACKGROUND};
    }}
    QWidget {{
        background-color: {LIGHT_BACKGROUND};
        color: {LIGHT_FOREGROUND};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE};
    }}
    QSplitter::handle {{ background: #BCC0CC; }}
    QGroupBox {{
        border: 1px solid #BCC0CC;
        border-radius: 8px;
        margin-top: 0.5em;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 10px;
        background-color: #DCE0E8;
        border-radius: 5px;
        color: {NEON_BLUE};
        font-weight: bold;
    }}

    /* Visualisation Box Style */
    QGroupBox#VisualisationBox {{
        border: 1px solid #BCC0CC;
    }}
    QGroupBox#VisualisationBox::title {{
        subcontrol-position: top left;
        padding-left: 10px;
    }}

    /* Status-specific coloring */
    QLabel#infoLabel[status="ok"] {{ color: {LIGHT_GREEN}; }}
    QLabel#infoLabel[status="error"] {{ color: {LIGHT_RED}; font-weight: bold; }}
    QLabel#rateLabel {{ color: #000000; }}

    QComboBox, QPushButton {{
        min-height: 28px;
    }}
    QComboBox {{
        background-color: #FFFFFF;
        border: 1px solid #BCC0CC;
        border-radius: 5px; padding: 5px;
        min-width: 80px;
    }}
    QComboBox:hover {{ background-color: #E6E9EF; }}
    QPushButton {{
        background-color: {NEON_BLUE};
        color: #FFFFFF;
        border: none; border-radius: 5px;
        padding: 6px 12px; font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {NEON_BLUE_HOVER}; }}
    
    QPushButton#themeButton {{
        background-color: transparent;
        border: 1px solid {NEON_BLUE};
        color: {LIGHT_FOREGROUND};
        font-size: 14pt;
        padding: 2px 8px;
    }}
    QPushButton#themeButton:hover {{ background-color: #DCE0E8; }}
    
    QPushButton#refreshButton {{
        background-color: {NEON_BLUE};
        border: none;
    }}
    QPushButton#refreshButton:hover {{ background-color: {NEON_BLUE_HOVER}; }}


    /* Disabled Styles */
    QComboBox:disabled, QPushButton:disabled {{
        background-color: #E6E9EF;
        color: #A6ADC8;
        border-color: #BCC0CC;
    }}
    QPushButton#refreshButton:disabled {{ background-color: #E6E9EF; }}

    /* Status Box Style (now a QWidget) */
    QWidget#statusBox {{
        background-color: #DCE0E8;
        border: 1px solid #BCC0CC;
        border-radius: 6px;
    }}
"""
