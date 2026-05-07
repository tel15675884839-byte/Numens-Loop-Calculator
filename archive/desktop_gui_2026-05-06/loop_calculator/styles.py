"""Palette and stylesheet helpers for the loop calculator."""

from __future__ import annotations

from collections.abc import Mapping


def _sp(value: int | float, scale: float) -> int:
    return max(1, int(round(value * scale)))


def palette(theme: str = "light") -> dict[str, str]:
    if theme == "industrial":
        return {
            "window": "#121417",         # Deep charcoal
            "surface": "#1E2124",        # Lighter gray
            "surface_alt": "#2A2E33",    # Section fill
            "surface_dark": "#0B0C0E",   # Sidebar background
            "sidebar": "#121417",
            "sidebar_item_hover": "#343A40",
            "text": "#F8F9FA",           # Near white
            "text_inv": "#ffffff",
            "muted": "#868E96",          # Slate gray
            "accent": "#E03131",         # Industrial Red (Danger)
            "accent_soft": "#410C0B",    # Dark Red tint
            "border": "#343A40",
            "hover": "#2C2E33",
            "success": "#51CF66",        # Neon green
            "success_soft": "#112F18",
            "danger": "#FA5252",
            "danger_soft": "#3D1A1A",
            "radius": "8px"
        }
    if theme == "dark":
        return {
            "window": "#0B0E14",         # Deeper black-blue
            "surface": "#141921",        # Dark gray-blue
            "surface_alt": "#1C232E",    # Lighter contrast
            "surface_soft": "#1A202A",
            "border": "#2D3643",
            "text": "#E6EDF5",           # High contrast light text
            "muted": "#8E9EB3",          # Muted slate
            "accent": "#58A6FF",         # Primary blue
            "accent_soft": "#1C3958",
            "danger": "#FF7B72",         # Soft red
            "danger_soft": "#3D1D1D",
            "success": "#7EE787",        # Soft green
            "success_soft": "#1E3526",
            "hover": "#212A35",
            "sidebar": "#090B0F",         # Deepest sidebar
            "sidebar_item_hover": "#1A202A",
            "shadow": "rgba(0, 0, 0, 0.4)",
        }
    return {
        "window": "#f0f2f5",
        "surface": "#ffffff",
        "surface_alt": "#f5f7fa",
        "surface_soft": "#f8f9fa",
        "border": "#dcdfe6",
        "text": "#000000",
        "muted": "#000000",
        "accent": "#409eff",
        "accent_soft": "#ecf5ff",
        "danger": "#f56c6c",
        "danger_soft": "#fef0f0",
        "success": "#67c23a",
        "success_soft": "#f0f9eb",
        "hover": "#ebf5ff",
        "sidebar": "#f8f9fa",
        "sidebar_item_hover": "#e4e7ed",
        "shadow": "rgba(0, 0, 0, 0.1)",
    }


def app_style(theme: str, ui_scale: float = 1.0) -> str:
    p = palette(theme)
    radius = p.get("radius", "8px")
    input_radius = "0px" if theme == "industrial" else "4px"
    s = lambda v: _sp(v, ui_scale)
    
    combo_arrow = "assets/combo-down-dark.svg" if theme in ("dark", "industrial") else "assets/combo-down.svg"
    spin_up = "assets/spin-up-dark.svg" if theme in ("dark", "industrial") else "assets/spin-up.svg"
    spin_down = "assets/spin-down-dark.svg" if theme in ("dark", "industrial") else "assets/spin-down.svg"
    
    return f"""
QMainWindow {{ background-color: {p['window']}; }}
QWidget {{ color: {p['text']}; font-family: 'Space Grotesk', 'Segoe UI', 'Inter', sans-serif; font-size: {s(13)}px; }}
QDialog, QMessageBox, QInputDialog {{ background-color: {p['surface']}; color: {p['text']}; }}
QMessageBox QLabel, QInputDialog QLabel {{ color: {p['text']}; background: transparent; }}
QDialogButtonBox QPushButton {{ min-height: {s(30)}px; padding: 0 {s(14)}px; border-radius: {s(6)}px; }}
QGroupBox {{ font-weight: bold; border: 1px solid {p['border']}; border-radius: {radius}; margin-top: {s(15)}px; padding: {s(15)}px; background-color: {p['surface']}; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: {s(10)}px; top: 1px; color: {p['muted']}; padding: 0 {s(4)}px; font-size: {s(10)}px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }}
QTableWidget, QTableView {{ border: none; border-left: 1px solid {p['border']}; border-top: 1px solid {p['border']}; gridline-color: {p['border']}; background-color: {p['surface']}; alternate-background-color: {p['surface']}; selection-background-color: {p['accent_soft']}; selection-color: {p['text']}; border-radius: 0px; outline: none; }}
QHeaderView::section {{ background-color: {p['window']}; color: {p['muted']}; border: none; border-bottom: 1px solid {p['border']}; border-right: 1px solid {p['border']}; padding: {s(6)}px; font-weight: bold; text-transform: uppercase; font-size: {s(10)}px; letter-spacing: 0.5px; }}
QLineEdit, QComboBox, QSpinBox {{ height: {s(32)}px; border: 1px solid {p['border']}; border-radius: {input_radius}; padding: 0 {s(8)}px; background: {p['surface']}; color: {p['text']}; font-size: {s(13)}px; font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-weight: 500; }}
QComboBox {{ padding-right: {s(22)}px; }}
QComboBox QAbstractItemView, QAbstractItemView {{ background: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']}; selection-background-color: {p['accent_soft']}; selection-color: {p['text']}; outline: none; }}
QComboBox QAbstractItemView::item:hover, QAbstractItemView::item:hover {{ background: transparent; color: {p['text']}; }}
QComboBox QAbstractItemView::item:selected:hover, QAbstractItemView::item:selected:hover {{ background: {p['accent_soft']}; color: {p['text']}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: {s(28)}px; border-left: 1px solid {p['border']}; background: {p['surface_alt']}; border-top-right-radius: {input_radius}; border-bottom-right-radius: {input_radius}; }}
QComboBox::down-arrow {{ image: url({combo_arrow}); width: {s(12)}px; height: {s(8)}px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: {s(16)}px; border-left: 1px solid {p['border']}; background: {p['surface_alt']}; }}
QSpinBox::up-arrow {{ image: url({spin_up}); width: {s(8)}px; height: {s(5)}px; }}
QSpinBox::down-arrow {{ image: url({spin_down}); width: {s(8)}px; height: {s(5)}px; }}
QFrame#sidebar {{ background-color: {p.get('sidebar', p['window'])}; border-right: 1px solid {p['border']}; }}
QFrame#pageHeader {{ background-color: {p['surface']}; border: 1px solid {p['border']}; border-radius: {s(12)}px; }}
QLabel#pageContext {{ color: {p['muted']}; }}
QLabel#loopSummary {{ color: {p['muted']}; }}
QFrame#accessRoleCard {{ background-color: {p['surface_alt']}; border: 1px solid {p['border']}; border-radius: {s(10)}px; }}
QLabel#accessRoleCardTitle {{ background: transparent; color: {p['text']}; font-size: {s(17)}px; font-weight: 800; }}
QLabel#accessRoleCardBody {{ background: transparent; color: {p['text']}; font-size: {s(15)}px; line-height: 1.45; }}
#resultSidebar {{
    background-color: {p.get('sidebar', p['window'])};
    border: 1px solid {p['border']};
    border-left: 1px solid {p['border']};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    border-bottom-left-radius: 0px;
}}
#resultSection {{ border: 1px solid {p['border']}; border-radius: 0px; background-color: transparent; }}
#sectionHeader {{ background-color: transparent; color: {p['text']}; font-weight: bold; padding: {s(4)}px 0px; border-bottom: 1px solid {p['border']}; font-size: {s(10)}px; text-transform: uppercase; letter-spacing: 1px; }}
#sidebarTitle {{ color: {p['muted']}; font-size: {s(11)}px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; }}
"""


def _button_rule(p: Mapping[str, str], *, color: str, border: str, bg: str, hover: str, weight: str = "normal") -> str:
    return (
        f"QPushButton {{ font-weight: {weight}; color: {color}; border: 1px solid {border}; "
        f"border-radius: 4px; background: {bg}; padding: 4px 12px; }}"
        f"QPushButton:hover {{ background: {hover}; }}"
    )

def primary_button_style(p: Mapping[str, str]) -> str:
    radius = p.get("radius", "8px")
    bg = p["accent"] if p.get("window") != "#f0f2f5" else p["accent_soft"]
    fg = "#ffffff" if p.get("window") != "#f0f2f5" else p["accent"]
    return (
        f"QPushButton {{ font-weight: 800; background-color: {bg}; border: 1px solid {p['accent']}; "
        f"color: {fg}; min-height: 34px; padding: 0 16px; border-radius: {radius}; text-transform: uppercase; font-size: 11px; letter-spacing: 0.6px; }}"
        f"QPushButton:hover {{ background-color: {p['accent_soft']}; color: {p['text']}; }}"
        f"QPushButton:disabled {{ color: {p['muted']}; border-color: {p['border']}; background-color: {p['surface_alt']}; }}"
    )


def secondary_button_style(p: Mapping[str, str]) -> str:
    radius = p.get("radius", "8px")
    return (
        f"QPushButton {{ background-color: {p['surface_alt']}; border: 1px solid {p['border']}; color: {p['text']}; "
        f"min-height: 34px; padding: 0 16px; border-radius: {radius}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }}"
        f"QPushButton:hover {{ background-color: {p['hover']}; border-color: {p['accent']}; color: {p['accent']}; }}"
        f"QPushButton:disabled {{ color: {p['muted']}; border-color: {p['border']}; }}"
    )


def primary_outline_button_style(p: Mapping[str, str]) -> str:
    radius = p.get("radius", "8px")
    return (
        f"QPushButton {{ font-weight: bold; color: {p['accent']}; border: 1px solid {p['accent']}; "
        f"border-radius: {radius}; background: {p['surface']}; min-height: 34px; padding: 0 16px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.6px; }}"
        f"QPushButton:hover {{ background: {p['accent_soft']}; }}"
    )


def danger_outline_button_style(p: Mapping[str, str]) -> str:
    radius = p.get("radius", "8px")
    return (
        f"QPushButton {{ color: {p['danger']}; border: 1px solid {p['danger']}; "
        f"border-radius: {radius}; background: {p['surface']}; min-height: 34px; padding: 0 16px; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }}"
        f"QPushButton:hover {{ background: {p['danger_soft']}; }}"
    )


def colored_outline_button_style(p: Mapping[str, str], color: str) -> str:
    radius = p.get("radius", "8px")
    hover_bg = p["accent_soft"] if color == p["accent"] else p["danger_soft"]
    return (
        f"QPushButton {{ font-weight: bold; color: {color}; border: 1px solid {color}; "
        f"border-radius: {radius}; background: {p['surface']}; min-height: 34px; padding: 0 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }}"
        f"QPushButton:hover {{ background: {hover_bg}; }}"
    )


def inline_input_style(p: Mapping[str, str]) -> str:
    return (
        f"QLineEdit {{"
        f" border: 1px solid {p['border']};"
        f" border-radius: 2px;"
        f" background: {p['surface']};"
        f" color: {p['text']};"
        f" font-family: 'Space Grotesk', 'Segoe UI', sans-serif;"
        f" font-size: 13px;"
        f" font-weight: 500;"
        f" padding: 0 8px;"
        f"}}"
    )


def diag_panel_style(p: Mapping[str, str], ok: bool = True) -> str:
    radius = p.get("radius", "8px")
    if ok:
        bg = "#0F3518"
        border = p["success"]
        tag = "#8EDAA0"
        state = "#F5FFF7"
        message = "#CFEFD6"
    else:
        bg = "#3D1A1A"
        border = p["danger"]
        tag = "#FFB3B3"
        state = "#FFF4F4"
        message = "#FFD6D6"
    return (
        f"QWidget#statusCard {{ background-color: {bg}; border-top: 5px solid {border}; border-radius: {radius}; }}"
        f"QLabel#statusCardTag {{ color: {tag}; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; }}"
        f"QLabel#statusCardState {{ color: {state}; font-size: 22px; font-weight: 900; font-family: 'Space Grotesk', 'Segoe UI', sans-serif; }}"
        f"QLabel#statusCardMessage {{ color: {message}; font-size: 12px; font-weight: 600; line-height: 1.3; }}"
    )


def tab_style(p: Mapping[str, str]) -> str:
    radius = p.get("radius", "8px")
    tab_radius = radius
    pane_radius = radius
    selected_text = p["text"] if p.get("window") == "#f0f2f5" else "white"
    return f"""
QTabWidget::pane {{ border: 1px solid {p['border']}; background: {p['surface']}; border-radius: {pane_radius}; margin-top: 6px; }}
QTabBar::tab {{ padding: 7px 42px 7px 14px; min-width: 88px; min-height: 30px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid {p['border']}; border-radius: {tab_radius}; background: {p['surface_alt']}; color: {p['muted']}; margin-right: 8px; margin-bottom: 2px; font-family: 'Space Grotesk'; font-weight: 800; }}
QTabBar::tab:hover {{ background: {p['hover']}; color: {p['text']}; border-color: {p['muted']}; }}
QTabBar::tab:selected {{ background: {p['accent']}; color: {selected_text}; font-weight: 900; border-color: {p['accent']}; }}
QTabBar::close-button {{ width: 0px; height: 0px; margin: 0px; padding: 0px; background: none; border: none; }}
"""


def close_tab_button_style(p: Mapping[str, str]) -> str:
    return (
        f"QPushButton {{"
        f"  border: none;"
        f"  background: transparent;"
        f"  color: {p['muted']};"
        f"  font-size: 16px;"
        f"  font-weight: 700;"
        f"  min-width: 18px;"
        f"  min-height: 18px;"
        f"  max-width: 18px;"
        f"  max-height: 18px;"
        f"  border-radius: 9px;"
        f"  margin: 0 10px 0 4px;"
        f"  padding: 0;"
        f"  text-align: center;"
        f"}}"
        f"QPushButton:hover {{"
        f"  color: {p['danger']};"
        f"  background: transparent;"
        f"}}"
    )


def panel_toggle_button_style(p: Mapping[str, str], selected: bool = False) -> str:
    radius = p.get("radius", "6px")
    if selected:
        return f"QPushButton {{ font-weight: bold; color: white; border: 1px solid {p['accent']}; border-radius: {radius}; background: {p['accent']}; padding: 6px 18px; }}"
    return (
        f"QPushButton {{ font-weight: bold; color: {p['text']}; border: 1px solid {p['border']}; border-radius: {radius}; "
        f"background: {p['surface_alt']}; padding: 6px 18px; }}"
        f"QPushButton:hover {{ border-color: {p['accent']}; color: {p['accent']}; }}"
    )
def sidebar_style(p: Mapping[str, str]) -> str:
    return f"background-color: {p['sidebar']}; border-right: 1px solid {p['border']};"


def nav_button_style(p: Mapping[str, str], selected: bool = False) -> str:
    radius = p.get("radius", "6px")
    if p.get("window") == "#121417": # Industrial Theme
        if selected:
            return f"QPushButton {{ background-color: #1B1F23; color: white; border: 1px solid transparent; border-left: 4px solid {p['accent']}; border-radius: 8px; text-align: left; padding: 13px 18px; font-weight: 900; font-family: 'Space Grotesk'; font-size: 12px; letter-spacing: 1px; }}"
        return f"QPushButton {{ background-color: transparent; color: #868E96; border: 1px solid transparent; border-radius: 8px; text-align: left; padding: 13px 18px; font-weight: 600; font-family: 'Space Grotesk'; font-size: 12px; letter-spacing: 1px; }} QPushButton:hover {{ color: white; background-color: #1B1F23; border-color: {p['border']}; }}"

    if selected:
        return f"QPushButton {{ background-color: {p['accent_soft']}; color: {p['text']}; border: 1px solid {p['accent']}; border-radius: {radius}; text-align: left; padding: 10px 15px; font-weight: bold; }}"
    return f"QPushButton {{ background-color: transparent; color: {p['text']}; border: none; border-radius: {radius}; text-align: left; padding: 10px 15px; }} QPushButton:hover {{ background-color: {p['sidebar_item_hover']}; color: {p['text']}; }}"


def unified_table_style(p: Mapping[str, str]) -> str:
    return f"""
QTableWidget, QTableView {{
    gridline-color: {p['border']};
    background-color: {p['surface']};
    alternate-background-color: {p['surface']};
    selection-background-color: {p['accent_soft']};
    selection-color: {p['text']};
    color: {p['text']};
    border-left: 1px solid {p['border']};
    border-top: 1px solid {p['border']};
    border-radius: 0px;
    outline: none;
}}
QTableWidget::item, QTableView::item {{
    padding: 8px;
    border: none;
}}
QTableWidget::item:selected,
QTableWidget::item:selected:!active,
QTableView::item:selected,
QTableView::item:selected:!active {{
    background: {p['accent_soft']};
    color: {p['text']};
}}
QTableWidget::item:hover,
QTableView::item:hover {{
    background: transparent;
    color: {p['text']};
}}
QTableWidget::item:selected:hover,
QTableView::item:selected:hover {{
    background: {p['accent_soft']};
    color: {p['text']};
}}
QTableWidget::item:focus,
QTableView::item:focus {{
    background: transparent;
    outline: none;
    border: none;
}}
QHeaderView::section {{
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 8px;
    background-color: {p['surface_alt']};
    border: none;
    border-bottom: 1px solid {p['border']};
    border-right: 1px solid {p['border']};
    color: {p['text']};
    font-weight: 800;
    font-size: 11px;
}}
"""


def device_combo_style(p: Mapping[str, str]) -> str:
    return f"""
QComboBox {{
    border: 1px solid {p['border']};
    border-radius: 4px;
    background: {p['surface']};
    color: {p['text']};
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 0 34px 0 12px;
    min-height: 30px;
    margin: 0;
    text-align: left;
}}
QComboBox:hover {{
    border: 1px solid {p['accent']};
    background: {p['surface_alt']};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border: none;
    background: {p['surface_alt']};
}}
QComboBox::drop-down:hover {{
    border: none;
    background: {p['hover']};
}}
QComboBox::down-arrow {{
    width: 12px;
    height: 8px;
}}
QComboBox QLineEdit {{
    border: none;
    background: {p['surface']};
    color: {p['text']};
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 0;
    margin: 0;
    qproperty-alignment: AlignLeft | AlignVCenter;
    selection-background-color: {p['accent_soft']};
    selection-color: {p['text']};
}}
QComboBox QAbstractItemView {{
    border: 1px solid {p['border']};
    background: {p['surface']};
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    selection-background-color: {p['accent_soft']};
    color: {p['text']};
}}
"""


def table_spinbox_style(p: Mapping[str, str]) -> str:
    return f"""
QSpinBox {{
    border: 1px solid {p['border']};
    border-radius: 2px;
    background: {p['surface']};
    color: {p['text']};
    padding: 0 8px;
    min-height: 32px;
    margin: 0;
    selection-background-color: {p['accent_soft']};
    selection-color: {p['text']};
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
}}
QSpinBox:hover {{
    border: 1px solid {p['border']};
    background: {p['surface']};
}}
QSpinBox:focus {{
    border: 1px solid {p['border']};
    background: {p['surface']};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    border: none;
    background: transparent;
}}
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 0px;
    height: 0px;
}}
QSpinBox QLineEdit {{
    border: none;
    background: {p['surface']};
    color: {p['text']};
    selection-background-color: {p['accent_soft']};
    selection-color: {p['text']};
    padding: 0;
    margin: 0;
    qproperty-alignment: AlignCenter;
}}
"""


def table_lineedit_style(p: Mapping[str, str]) -> str:
    return f"""
QLineEdit {{
    border: 1px solid {p['border']};
    border-radius: 2px;
    background: {p['surface']};
    color: {p['text']};
    padding: 0 8px;
    min-height: 32px;
    margin: 0;
    selection-background-color: {p['accent_soft']};
    selection-color: {p['text']};
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
}}
QLineEdit:hover {{
    border: 1px solid {p['border']};
    background: {p['surface']};
}}
QLineEdit:focus {{
    border: 1px solid {p['border']};
    background: {p['surface']};
}}
"""


def card_style(p: Mapping[str, str]) -> str:
    return f"background-color: {p['surface']}; border: 1px solid {p['border']}; border-radius: 12px;"


def indicator_style(p: Mapping[str, str], state: str = "normal") -> str:
    colors = {
        "normal": (p["accent_soft"], p["accent"]),
        "success": (p["success_soft"], p["success"]),
        "danger": (p["danger_soft"], p["danger"]),
    }
    bg, fg = colors.get(state, colors["normal"])
    return f"background-color: {bg}; color: {fg}; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 10px; text-transform: uppercase;"
