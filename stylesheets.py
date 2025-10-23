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
    
    QComboBox, QPushButton {{
        min-height: 28px;
    }}
    QComboBox, QSpinBox {{
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 5px; padding: 5px;
        min-width: 60px;
    }}
    QComboBox:hover, QSpinBox:hover {{ background-color: #45475A; }}
    QSpinBox {{ padding: 2px; }}

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

    /* Tab styles */
    QTabWidget::pane {{
        border: 1px solid #45475A;
        border-top: none;
        border-radius: 0 0 5px 5px;
    }}
    QTabBar::tab {{
        background: #313244;
        border: 1px solid #45475A;
        border-bottom: none;
        padding: 8px 15px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }}
    QTabBar::tab:hover {{
        background: #45475A;
    }}
    QTabBar::tab:selected {{
        background: {DARK_BACKGROUND};
        border: 1px solid {NEON_BLUE};
        border-bottom: 1px solid {DARK_BACKGROUND};
    }}

    /* Dummy panel in grid view */
    QFrame#dummyImuPanel {{
        border: 2px dashed #45475A;
        border-radius: 5px;
        background-color: #313244;
    }}
    QFrame#dummyImuPanel {{
        border: 2px dashed #45475A;
        border-radius: 5px;
        background-color: #313244;
    }}

    /* New style for grid panel title */
    QLabel#ImuGridTitleLabel {{
        background-color: #313244;
        color: {NEON_BLUE_HOVER};
        padding: 4px;
        border-radius: 3px;
        font-weight: bold;
    }}
    /* Disabled Styles */
    QComboBox:disabled, QPushButton:disabled, QSpinBox:disabled, QCheckBox:disabled {{
        background-color: #313244;
        color: #6C7086;
        border-color: #45475A;
    }}
    QPushButton#refreshButton:disabled {{ background-color: #313244; }}
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

    QComboBox, QPushButton {{
        min-height: 28px;
    }}
    QComboBox, QSpinBox {{
        background-color: #FFFFFF;
        border: 1px solid #BCC0CC;
        border-radius: 5px; padding: 5px;
        min-width: 60px;
    }}
    QComboBox:hover, QSpinBox:hover {{ background-color: #E6E9EF; }}
    QSpinBox {{ padding: 2px; }}

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

    /* Tab styles */
    QTabWidget::pane {{
        border: 1px solid #BCC0CC;
        border-top: none;
        border-radius: 0 0 5px 5px;
    }}
    QTabBar::tab {{
        background: #DCE0E8;
        border: 1px solid #BCC0CC;
        border-bottom: none;
        padding: 8px 15px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }}
    QTabBar::tab:hover {{
        background: #E6E9EF;
    }}
    QTabBar::tab:selected {{
        background: {LIGHT_BACKGROUND};
        border: 1px solid {NEON_BLUE};
        border-bottom: 1px solid {LIGHT_BACKGROUND};
    }}

    /* Dummy panel in grid view */
    QFrame#dummyImuPanel {{
        border: 2px dashed #BCC0CC;
        border-radius: 5px;
        background-color: #E6E9EF;
    }}
    QFrame#dummyImuPanel {{
        border: 2px dashed #BCC0CC;
        border-radius: 5px;
        background-color: #E6E9EF;
    }}

    /* New style for grid panel title */
    QLabel#ImuGridTitleLabel {{
        background-color: #DCE0E8;
        color: {NEON_BLUE};
        padding: 4px;
        border-radius: 3px;
        font-weight: bold;
    }}
    /* Disabled Styles */
    QComboBox:disabled, QPushButton:disabled, QSpinBox:disabled, QCheckBox:disabled {{
        background-color: #E6E9EF;
        color: #A6ADC8;
        border-color: #BCC0CC;
    }}
    QPushButton#refreshButton:disabled {{ background-color: #E6E9EF; }}
"""
