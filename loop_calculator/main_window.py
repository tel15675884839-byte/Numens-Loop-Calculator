from __future__ import annotations

import os
import sys
import ctypes
import shutil

from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPalette, QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
    QStyle,
)

from loop_calculator.constants import PANEL_SPECS
from loop_calculator.app_settings import AppSettings
from loop_calculator.database import ProductDatabase
from loop_calculator.i18n import LANGUAGE_OPTIONS, tr_text, get_theme_name
from loop_calculator.loop_editor import LoopEditorWidget
from loop_calculator.product_manager import ProductManagerWidget
from loop_calculator.styles import app_style, palette
from loop_calculator.utils import set_message_box_texts


class CIEMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "en"
        self.theme = "industrial" # Default to dark industrial theme
        self.ui_scale = self._detect_ui_scale()
        app = QApplication.instance()
        if app is not None and self.ui_scale < 1.0:
            app.setFont(QFont("Segoe UI", max(8, self._s(9))))
        self.p = palette(self.theme)
        self.project_dir = os.path.dirname(os.path.dirname(__file__))
        self.settings = AppSettings(self.project_dir)
        self.product_db = ProductDatabase(self.project_dir)
        self.panel_type = "Standard"
        self._syncing = False
        self._syncing_loop_device_limit = False
        self._syncing_loop_min_voltage = False
        self.auth_level = 0
        self.panel_workspace = None

        self._apply_initial_window_size()
        self.workspace_page = QWidget()
        self.setCentralWidget(self.workspace_page)
        self._create_workspace_page()
        self._ensure_workspace_state()
        self.apply_theme(self.theme)
        self.retranslate_ui()
        self._load_workspace()

        icon_path = os.path.join(self.project_dir, "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def t(self, key, **kwargs):
        return tr_text(self.lang, key, **kwargs)

    def _s(self, value: int) -> int:
        return max(1, int(round(value * self.ui_scale)))

    def _detect_ui_scale(self) -> float:
        app = QApplication.instance()
        if app is None:
            return 1.0
        screen = app.primaryScreen()
        if screen is None:
            return 1.0
        available = screen.availableGeometry()
        design_w, design_h = 1400, 900
        if available.width() < design_w or available.height() < design_h:
            return 0.9
        return 1.0

    def _apply_initial_window_size(self) -> None:
        app = QApplication.instance()
        if app is None or app.primaryScreen() is None:
            self.resize(self._s(1400), self._s(900))
            return
        available = app.primaryScreen().availableGeometry()
        margin = 24
        target_w = min(self._s(1400), max(800, available.width() - margin))
        target_h = min(self._s(900), max(620, available.height() - margin))
        self.resize(target_w, target_h)

    def _create_pref_controls(self, layout):
        col = QVBoxLayout()
        col.setSpacing(12)
        col.setContentsMargins(0, 0, 0, 0)
        
        theme_v = QVBoxLayout()
        theme_v.setSpacing(4)
        self.lbl_theme = QLabel()
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(self._s(208))
        self.theme_combo.currentIndexChanged.connect(lambda: self._on_theme_changed(self.theme_combo.currentData()))
        theme_v.addWidget(self.lbl_theme)
        theme_v.addWidget(self.theme_combo)
        col.addLayout(theme_v)
        
        lang_v = QVBoxLayout()
        lang_v.setSpacing(4)
        self.lbl_lang = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(self._s(208))
        self.lang_combo.currentIndexChanged.connect(lambda: self._on_lang_changed(self.lang_combo.currentData()))
        lang_v.addWidget(self.lbl_lang)
        lang_v.addWidget(self.lang_combo)
        col.addLayout(lang_v)
        
        layout.addLayout(col)

    def _create_access_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.lbl_access_intro = QLabel()
        self.lbl_access_intro.setWordWrap(True)
        layout.addWidget(self.lbl_access_intro)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.access_status_group = QGroupBox()
        status_layout = QVBoxLayout(self.access_status_group)
        status_layout.setSpacing(10)
        self.lbl_access_status_card = QLabel()
        self.lbl_access_status_card.setObjectName("accessStatusValue")
        self.lbl_access_status_hint = QLabel()
        self.lbl_access_status_hint.setWordWrap(True)
        status_layout.addWidget(self.lbl_access_status_card)
        status_layout.addWidget(self.lbl_access_status_hint)
        status_layout.addStretch()
        top_row.addWidget(self.access_status_group, 1)

        self.access_actions_group = QGroupBox()
        actions_layout = QGridLayout(self.access_actions_group)
        actions_layout.setHorizontalSpacing(14)
        actions_layout.setVerticalSpacing(12)
        self.btn_admin_login = QPushButton()
        self.btn_factory_login = QPushButton()
        self.btn_logout = QPushButton()
        self.btn_passwords = QPushButton()
        self.btn_admin_login.clicked.connect(self._login_admin)
        self.btn_factory_login.clicked.connect(self._login_factory)
        self.btn_logout.clicked.connect(self._logout)
        self.btn_passwords.clicked.connect(self._change_passwords)
        actions_layout.addWidget(self.btn_admin_login, 0, 0)
        actions_layout.addWidget(self.btn_factory_login, 0, 1)
        actions_layout.addWidget(self.btn_logout, 1, 0)
        actions_layout.addWidget(self.btn_passwords, 1, 1)
        top_row.addWidget(self.access_actions_group, 1)

        layout.addLayout(top_row)

        self.access_notes_group = QGroupBox()
        notes_layout = QVBoxLayout(self.access_notes_group)
        notes_layout.setSpacing(12)
        self.lbl_access_notes = QLabel()
        self.lbl_access_notes.setWordWrap(True)
        notes_layout.addWidget(self.lbl_access_notes)
        role_cards = QHBoxLayout()
        role_cards.setSpacing(12)
        self.access_role_cards: dict[str, tuple[QLabel, QLabel]] = {}
        for role_key in ("view", "admin", "factory"):
            card = QFrame()
            card.setObjectName("accessRoleCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 14, 14, 14)
            card_layout.setSpacing(8)
            title = QLabel()
            title.setObjectName("accessRoleCardTitle")
            body = QLabel()
            body.setObjectName("accessRoleCardBody")
            body.setWordWrap(True)
            card_layout.addWidget(title)
            card_layout.addWidget(body)
            card_layout.addStretch()
            role_cards.addWidget(card, 1)
            self.access_role_cards[role_key] = (title, body)
        notes_layout.addLayout(role_cards)
        layout.addWidget(self.access_notes_group)
        layout.addStretch()
        return page

    def _create_workspace_page(self):
        main_layout = QHBoxLayout(self.workspace_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(self._s(264))
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(self._s(18), self._s(22), self._s(18), self._s(18))
        sidebar_layout.setSpacing(self._s(12))

        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_logo.setFixedHeight(self._s(76))
        self.lbl_logo.setCursor(Qt.PointingHandCursor)
        self.lbl_logo.mouseDoubleClickEvent = self._handle_logo_double_click
        self._refresh_logo()
        sidebar_layout.addWidget(self.lbl_logo)

        self.nav_btns = {}
        for key in ["loops", "database_menu", "auth_access"]:
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self._on_nav_clicked(k))
            sidebar_layout.addWidget(btn)
            self.nav_btns[key] = btn
        sidebar_layout.addStretch()
        self._create_pref_controls(sidebar_layout)
        self.sidebar_site_label = QLabel("")
        self.sidebar_site_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sidebar_site_label.setCursor(Qt.PointingHandCursor)
        self.sidebar_site_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.sidebar_site_label.setOpenExternalLinks(False)
        self.sidebar_site_label.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        sidebar_layout.addWidget(self.sidebar_site_label)
        
        main_layout.addWidget(self.sidebar)

        # Content Area
        content_container = QWidget()
        self.content_layout = QVBoxLayout(content_container)
        self.content_layout.setContentsMargins(self._s(24), self._s(18), self._s(24), self._s(24))
        self.content_layout.setSpacing(self._s(18))

        self.page_header = QFrame()
        self.page_header.setObjectName("pageHeader")
        page_header_layout = QVBoxLayout(self.page_header)
        page_header_layout.setContentsMargins(self._s(20), self._s(18), self._s(20), self._s(18))
        page_header_layout.setSpacing(self._s(4))
        self.lbl_page_context = QLabel()
        self.lbl_page_context.setObjectName("pageContext")
        self.lbl_page_title = QLabel("DASHBOARD")
        page_header_layout.addWidget(self.lbl_page_context)
        page_header_layout.addWidget(self.lbl_page_title)
        self.content_layout.addWidget(self.page_header)

        # Stacked Pages
        self.stack = QStackedWidget()
        
        # Page 1: Loops (Current UI)
        self.loops_page = QWidget()
        loops_layout = QVBoxLayout(self.loops_page)
        loops_layout.setContentsMargins(0, 0, 0, 0)
        loops_layout.setSpacing(self._s(12))

        loops_header = QHBoxLayout()
        loops_header.setContentsMargins(0, 0, 0, 0)
        loops_header.setSpacing(self._s(12))
        self.lbl_loop_summary = QLabel()
        self.lbl_loop_summary.setObjectName("loopSummary")
        loops_header.addWidget(self.lbl_loop_summary)
        loops_header.addStretch()

        self.btn_add_loop = QPushButton()
        self.btn_add_loop.clicked.connect(lambda: self._add_loop())
        self.btn_add_loop.setCursor(Qt.PointingHandCursor)
        loops_header.addWidget(self.btn_add_loop)
        loops_layout.addLayout(loops_header)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabCloseRequested.connect(self._close_loop)
        self.tab_widget.currentChanged.connect(self._update_add_button_pos)
        loops_layout.addWidget(self.tab_widget)

        self.stack.addWidget(self.loops_page)
        
        # Page 2: Product DB
        self.db_page = ProductManagerWidget(self.product_db, self)
        self.db_page.data_changed.connect(self.reload_products)
        self.stack.addWidget(self.db_page)

        # Page 3: Access
        self.access_page = self._create_access_page()
        self.stack.addWidget(self.access_page)
        
        self.content_layout.addWidget(self.stack)
        main_layout.addWidget(content_container)

    def _on_nav_clicked(self, key):
        if key == "loops":
             self.stack.setCurrentWidget(self.loops_page)
        elif key == "database_menu":
             self.stack.setCurrentWidget(self.db_page)
             self.db_page.refresh_data()
        elif key == "auth_access":
             self.stack.setCurrentWidget(self.access_page)
        self._update_page_header(key)
        self._apply_nav_styles(key)

    def _apply_nav_styles(self, active_key="loops"):
        from .styles import nav_button_style
        for key, btn in self.nav_btns.items():
            if key == "auth_access":
                btn.setText(self._access_nav_label())
            else:
                btn.setText(self.t(key).upper())
            btn.setStyleSheet(nav_button_style(self.p, selected=(key == active_key)))

    def _fill_pref_combos(self):
        self._syncing = True
        try:
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            for code in ["light", "dark", "industrial"]:
                self.theme_combo.addItem(get_theme_name(self.lang, code), code)
            self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.theme))
            self.theme_combo.blockSignals(False)

            self.lang_combo.blockSignals(True)
            self.lang_combo.clear()
            for code, label in LANGUAGE_OPTIONS.items():
                self.lang_combo.addItem(label, code)
            self.lang_combo.setCurrentIndex(self.lang_combo.findData(self.lang))
            self.lang_combo.blockSignals(False)
        finally:
            self._syncing = False

    def _on_theme_changed(self, theme_code):
        if not self._syncing and theme_code and theme_code != self.theme:
            self.apply_theme(theme_code)

    def _on_lang_changed(self, lang_code):
        if not self._syncing and lang_code and lang_code != self.lang:
            self.lang = lang_code
            self.retranslate_ui()

    def apply_theme(self, theme):
        self.theme = theme
        self.p = palette(theme)
        current_style = app_style(theme, self.ui_scale)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(current_style)
        self.setStyleSheet(current_style)
        self._fill_pref_combos()
        self._apply_local_theme()
        if hasattr(self, "db_page"):
            self.db_page.apply_style(self.p)
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loop.refresh_theme()
        
        # Apply native dark title bar for Windows
        self._set_native_dark_title_bar(theme in ["dark", "industrial"])

    def _set_native_dark_title_bar(self, dark: bool, target_widget: QWidget | None = None):
        """Enable or disable native dark mode for the Windows title bar of a window."""
        if sys.platform != "win32":
            return
            
        widget = target_widget or self
        try:
            # DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 11: 20, Windows 10: 19)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_dark = ctypes.c_int(1 if dark else 0)
            
            # Get window handle
            hwnd = widget.winId()
            if not isinstance(hwnd, int):
                hwnd = int(hwnd)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(set_dark), 
                ctypes.sizeof(set_dark)
            )
            
            # If it's a secondary window, make sure it has the app stylesheet
            if target_widget and target_widget != self:
                # IMPORTANT: Set stylesheet specifically on the dialog to overwrite defaults
                target_widget.setStyleSheet(app_style(self.theme, self.ui_scale))
                # Also set the palette to ensure system colors (like scrollbar areas) are correct
                p = QPalette()
                p.setColor(QPalette.Window, QColor(self.p['window']))
                p.setColor(QPalette.WindowText, QColor(self.p['text']))
                p.setColor(QPalette.Base, QColor(self.p['surface']))
                p.setColor(QPalette.Text, QColor(self.p['text']))
                target_widget.setPalette(p)

            # Force update the title bar rendering
            title = widget.windowTitle()
            widget.setWindowTitle(title + " ")
            widget.setWindowTitle(title)
        except Exception:
            pass # Fail gracefully 

    def retranslate_ui(self):
        self.setWindowTitle(self.t("app_title"))
        self.lbl_theme.setText(self.t("theme").upper())
        self.lbl_lang.setText(self.t("language").upper())
        self.btn_admin_login.setText(self.t("auth_admin_login"))
        self.btn_factory_login.setText(self.t("auth_factory_login"))
        self.btn_logout.setText(self.t("auth_logout"))
        self.btn_passwords.setText(self.t("auth_change_passwords"))
        self.lbl_access_intro.setText(self.t("auth_access_intro"))
        self.access_status_group.setTitle(self.t("auth_current_access_level").upper())
        self.access_actions_group.setTitle(self.t("auth_actions").upper())
        self.access_notes_group.setTitle(self.t("auth_permission_notes").upper())
        self.lbl_access_notes.setText(self.t("auth_permission_notes_body"))
        self.access_role_cards["view"][0].setText(self.t("auth_view_role"))
        self.access_role_cards["view"][1].setText(self.t("auth_view_description"))
        self.access_role_cards["admin"][0].setText(self.t("auth_admin_role"))
        self.access_role_cards["admin"][1].setText(self.t("auth_admin_description"))
        self.access_role_cards["factory"][0].setText(self.t("auth_factory_role"))
        self.access_role_cards["factory"][1].setText(self.t("auth_factory_description"))
        self.lbl_logo.setToolTip(self.t("logo_replace_tooltip"))
        self._fill_pref_combos()
        self.btn_add_loop.setText(self.t("add_loop"))
        website = self.t("website_url")
        self.sidebar_site_label.setText(f'<a href="https://{website}" style="text-decoration:none;">{website}</a>')
        self._resync_tab_names()
        self._update_page_header(self._get_active_nav_key())
        self._apply_nav_styles(self._get_active_nav_key())
        if hasattr(self, "db_page"):
            self.db_page.retranslate_ui()
            self.db_page.refresh_permissions()
        self._update_access_status()
        self._apply_local_theme()

    def _get_active_nav_key(self):
        if self.stack.currentWidget() == self.loops_page:
            return "loops"
        if self.stack.currentWidget() == self.db_page:
            return "database_menu"
        if self.stack.currentWidget() == self.access_page:
            return "auth_access"
        return "loops"

    def _apply_local_theme(self):
        self.lbl_logo.setStyleSheet(f"margin-bottom: {self._s(16)}px;")
        self._refresh_logo()
        label_style = f"font-weight: bold; color: {self.p['muted']}; font-size: {self._s(10)}px; text-transform: uppercase; letter-spacing: 0.5px;"
        self.lbl_theme.setStyleSheet(label_style)
        self.lbl_lang.setStyleSheet(label_style)
        self.sidebar_site_label.setStyleSheet(f"QLabel {{ color: {self.p['danger']}; font-weight: 700; font-size: {self._s(12)}px; }} QLabel:hover {{ color: {self.p['accent']}; }}")
        self.lbl_page_context.setStyleSheet(f"color: {self.p['muted']}; font-size: {self._s(11)}px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;")
        self.lbl_page_title.setStyleSheet(f"font-weight: 900; font-size: {self._s(26)}px; color: {self.p['text']};")
        self.lbl_loop_summary.setStyleSheet(f"color: {self.p['muted']}; font-size: {self._s(12)}px; font-weight: 600;")
        self.lbl_access_intro.setStyleSheet(f"color: {self.p['muted']}; font-size: {self._s(12)}px; padding: 0 0 {self._s(2)}px {self._s(2)}px;")
        self.lbl_access_status_card.setStyleSheet(f"color: {self.p['text']}; font-size: {self._s(24)}px; font-weight: 900;")
        self.lbl_access_status_hint.setStyleSheet(f"color: {self.p['muted']}; font-size: {self._s(12)}px; line-height: 1.4;")
        self.lbl_access_notes.setStyleSheet(f"color: {self.p['text']}; font-size: {self._s(12)}px; line-height: 1.5;")
        self.tab_widget.setStyleSheet(self.tab_style())
        self.btn_add_loop.setStyleSheet(self.primary_outline_button_style())
        self.btn_admin_login.setStyleSheet(self.secondary_button_style())
        self.btn_factory_login.setStyleSheet(self.primary_button_style())
        self.btn_logout.setStyleSheet(self.secondary_button_style())
        self.btn_passwords.setStyleSheet(self.secondary_button_style())
        self.btn_add_loop.setFixedHeight(self._s(38))
        self.btn_add_loop.setMinimumWidth(self._s(124))
        for button in [self.btn_admin_login, self.btn_factory_login, self.btn_logout, self.btn_passwords]:
            button.setMinimumHeight(self._s(42))
        self._apply_nav_styles(self._get_active_nav_key())
        self._apply_panel_button_styles()
        self._refresh_close_buttons()
        self._update_add_button_pos()
        self._update_access_status()

    def primary_button_style(self):
        from .styles import primary_button_style
        return primary_button_style(self.p)

    def secondary_button_style(self):
        from .styles import secondary_button_style
        return secondary_button_style(self.p)

    def primary_outline_button_style(self):
        from .styles import primary_outline_button_style
        return primary_outline_button_style(self.p)

    def danger_outline_button_style(self):
        from .styles import danger_outline_button_style
        return danger_outline_button_style(self.p)

    def colored_outline_button_style(self, color):
        from .styles import colored_outline_button_style
        return colored_outline_button_style(self.p, color)

    def inline_input_style(self):
        return (
            f"border: 1px solid {self.p['border']}; border-radius: 2px; background: {self.p['surface']}; "
            f"color: {self.p['text']}; padding: 0 2px;"
        )

    def diag_panel_style(self, ok=True):
        from .styles import diag_panel_style
        return diag_panel_style(self.p, ok)

    def tab_style(self):
        from .styles import tab_style
        return tab_style(self.p)

    def close_tab_button_style(self):
        from .styles import close_tab_button_style
        return close_tab_button_style(self.p)

    def panel_toggle_button_style(self, selected=False):
        from .styles import panel_toggle_button_style
        return panel_toggle_button_style(self.p, selected)

    def _apply_panel_button_styles(self):
        pass

    def _auth_label(self) -> str:
        if self.auth_level >= 2:
            return self.t("auth_factory_mode")
        if self.auth_level >= 1:
            return self.t("auth_admin_mode")
        return self.t("auth_view_mode")

    def _auth_role_name(self) -> str:
        if self.auth_level >= 2:
            return self.t("auth_factory_role")
        if self.auth_level >= 1:
            return self.t("auth_admin_role")
        return self.t("auth_view_role")

    def _auth_role_description(self) -> str:
        if self.auth_level >= 2:
            return self.t("auth_factory_description")
        if self.auth_level >= 1:
            return self.t("auth_admin_description")
        return self.t("auth_view_description")

    def _access_nav_label(self) -> str:
        return f"{self.t('auth_access').upper()} · {self._auth_role_name().upper()}"

    def _update_access_status(self) -> None:
        is_factory = self.auth_level >= 2
        is_logged_in = self.auth_level > 0
        self.lbl_access_status_card.setText(self._auth_role_name())
        self.lbl_access_status_hint.setText(self._auth_role_description())
        self.btn_passwords.setEnabled(is_factory)
        self.btn_logout.setEnabled(is_logged_in)
        self.btn_admin_login.setEnabled(self.auth_level < 1)
        self.btn_factory_login.setEnabled(self.auth_level < 2)
        self._apply_nav_styles(self._get_active_nav_key())

    def _access_nav_label(self) -> str:
        return f"{self.t('auth_access').upper()} / {self._auth_role_name().upper()}"

    def _update_access_status(self) -> None:
        is_factory = self.auth_level >= 2
        is_logged_in = self.auth_level > 0
        self.lbl_access_status_card.setText(self._auth_role_name())
        self.lbl_access_status_hint.setText(self._auth_role_description())
        self.btn_passwords.setEnabled(is_factory)
        self.btn_logout.setEnabled(is_logged_in)
        self.btn_admin_login.setEnabled(self.auth_level < 1)
        self.btn_factory_login.setEnabled(self.auth_level < 2)
        self._update_page_header(self._get_active_nav_key())
        self._apply_nav_styles(self._get_active_nav_key())

    def _page_context_text(self, key: str) -> str:
        if key == "database_menu":
            return f"{len(self.product_db.products)} product records loaded"
        if key == "auth_access":
            return f"Current role: {self._auth_role_name()}"
        loop_count = self.tab_widget.count() if hasattr(self, "tab_widget") else 0
        suffix = "tab" if loop_count == 1 else "tabs"
        return f"{loop_count} active loop {suffix}"

    def _update_page_header(self, key: str) -> None:
        title_key = "auth_access" if key == "auth_access" else key
        self.lbl_page_title.setText(self.t(title_key).upper())
        self.lbl_page_context.setText(self._page_context_text(key))

    def _ask_password(self, role: str) -> bool:
        title = self.t("auth_admin_login") if role == "admin" else self.t("auth_factory_login")
        label = self.t("auth_password_prompt", role=role.title())
        value, ok = QInputDialog.getText(self, title, label, QLineEdit.Password)
        if not ok:
            return False
        expected = self.settings.admin_password if role == "admin" else self.settings.factory_password
        if value != expected:
            QMessageBox.warning(self, self.t("notice_title"), self.t("auth_password_incorrect"))
            return False
        return True

    def _login_admin(self) -> None:
        if self._ask_password("admin"):
            self.auth_level = max(self.auth_level, 1)
            self._on_auth_changed()

    def _login_factory(self) -> None:
        if self._ask_password("factory"):
            self.auth_level = 2
            self._on_auth_changed()

    def _logout(self) -> None:
        self.auth_level = 0
        self._on_auth_changed()

    def _on_auth_changed(self) -> None:
        self._update_access_status()
        if hasattr(self, "db_page"):
            self.db_page.refresh_permissions()

    def _change_passwords(self) -> None:
        if self.auth_level < 2:
            QMessageBox.warning(self, self.t("notice_title"), self.t("auth_factory_required"))
            return
        admin_password, ok = QInputDialog.getText(
            self, self.t("auth_change_passwords"), self.t("auth_new_admin_password"), QLineEdit.Password
        )
        admin_password = admin_password.strip()
        if not ok:
            return
        if not admin_password:
            QMessageBox.warning(self, self.t("notice_title"), self.t("auth_password_empty"))
            return
        factory_password, ok = QInputDialog.getText(
            self, self.t("auth_change_passwords"), self.t("auth_new_factory_password"), QLineEdit.Password
        )
        factory_password = factory_password.strip()
        if not ok:
            return
        if not factory_password:
            QMessageBox.warning(self, self.t("notice_title"), self.t("auth_password_empty"))
            return
        self.settings.set_passwords(admin_password, factory_password)
        QMessageBox.information(self, self.t("notice_title"), self.t("auth_passwords_saved"))

    def _restore_default_data(self) -> None:
        if self.auth_level < 2:
            QMessageBox.warning(self, self.t("notice_title"), self.t("auth_factory_required"))
            return
        if self._question("restore_default_data", "restore_default_confirm") != QMessageBox.Yes:
            return
        self.product_db.restore_default_products()
        if hasattr(self, "db_page"):
            self.db_page.refresh_data()
        self.reload_products(refresh_only=True)
        QMessageBox.information(self, self.t("notice_title"), self.t("restore_default_success"))

    def _default_logo_path(self) -> str:
        return os.path.join(self.project_dir, "assets", "logo.png")

    def _resolved_logo_path(self) -> str:
        if self.theme == "light":
            candidate = os.path.join(self.project_dir, "assets", "3e928fa4fee496a06f6771c85c72cc24.png")
            if os.path.exists(candidate):
                return candidate

        custom = self.settings.custom_logo_path
        if custom:
            candidate = os.path.join(self.project_dir, custom)
            if os.path.exists(candidate):
                return candidate
        return self._default_logo_path()

    def _refresh_logo(self) -> None:
        logo_path = self._resolved_logo_path()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.lbl_logo.setPixmap(pixmap.scaled(self._s(224), self._s(62), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _handle_logo_double_click(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        if not self._ask_password("factory"):
            return
        QMessageBox.information(self, self.t("notice_title"), self.t("logo_replace_format_hint"))
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.t("logo_replace_dialog_title"),
            self.project_dir,
            "Image Files (*.png *.jpg *.jpeg *.bmp)",
        )
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1].lower() or ".png"
        target_relative = os.path.join("assets", f"custom_logo{ext}")
        target_path = os.path.join(self.project_dir, target_relative)
        shutil.copy2(file_path, target_path)
        self.settings.set_custom_logo_path(target_relative)
        self._refresh_logo()
        QMessageBox.information(self, self.t("notice_title"), self.t("logo_replace_success"))

    def _refresh_close_buttons(self):
        for index in range(self.tab_widget.count()):
            button = self.tab_widget.tabBar().tabButton(index, QTabBar.RightSide)
            if isinstance(button, QPushButton):
                button.setStyleSheet(self.close_tab_button_style())

    def _question(self, title_key, msg_key, **kwargs):
        box = QMessageBox(QMessageBox.Question, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        self._set_native_dark_title_bar(self.theme in ["dark", "industrial"], box)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        set_message_box_texts(box, self)
        return box.exec()

    def _info(self, title_key, msg_key, **kwargs):
        box = QMessageBox(QMessageBox.Information, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        self._set_native_dark_title_bar(self.theme in ["dark", "industrial"], box)
        box.setStandardButtons(QMessageBox.Ok)
        set_message_box_texts(box, self)
        return box.exec()

    def _default_workspace_state(self):
        return {
            "panel_type": self.panel_type,
            "current_index": 0,
            "loops": [
                {
                    "panel_type": self.panel_type,
                    "addr_limit_index": 0,
                    "cable_index": 1,
                    "min_voltage": "17",
                    "aux_current": "0",
                    "rows": [],
                }
            ],
        }

    def _ensure_workspace_state(self):
        if self.panel_workspace is None:
            self.panel_workspace = self._default_workspace_state()

    def _capture_current_workspace(self):
        loops = []
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loops.append(loop.export_state())
        if not loops:
            loops = self._default_workspace_state()["loops"]
        self.panel_workspace = {
            "panel_type": self.panel_type,
            "current_index": max(0, self.tab_widget.currentIndex()),
            "loops": loops,
        }

    def _clear_tab_widget(self):
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

    def _load_workspace(self):
        self._ensure_workspace_state()
        state = self.panel_workspace
        self._clear_tab_widget()
        for loop_state in state.get("loops", []):
            self._add_loop(copy_prompt=False, loop_state=loop_state)
        if self.tab_widget.count() == 0:
            self._add_loop(copy_prompt=False)
        self.tab_widget.setCurrentIndex(min(state.get("current_index", 0), self.tab_widget.count() - 1))
        self._update_loop_label()
        self._recalc_global_battery()

    def _switch_panel(self, panel_type):
        pass

    def _update_loop_label(self):
        pass

    def _resync_tab_names(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabText(index, self.t("loop_tab_name", index=index + 1))

    def _iter_loops(self) -> list[LoopEditorWidget]:
        loops: list[LoopEditorWidget] = []
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loops.append(loop)
        return loops

    def _sync_loop_addr_limit(self, source_loop: LoopEditorWidget, index: int) -> None:
        if self._syncing_loop_device_limit:
            return
        if index < 0:
            return
        self._syncing_loop_device_limit = True
        try:
            for loop in self._iter_loops():
                if loop is source_loop:
                    continue
                if loop.combo_addr_limit.currentIndex() != index:
                    loop.combo_addr_limit.setCurrentIndex(index)
        finally:
            self._syncing_loop_device_limit = False

    def _sync_loop_min_voltage(self, source_loop: LoopEditorWidget, value: str) -> None:
        if self._syncing_loop_min_voltage:
            return
        self._syncing_loop_min_voltage = True
        try:
            for loop in self._iter_loops():
                if loop is source_loop:
                    continue
                if loop.edit_min_voltage.text() != value:
                    loop.edit_min_voltage.setText(value)
        finally:
            self._syncing_loop_min_voltage = False

    def _add_loop(self, copy_prompt=True, loop_state=None):
        spec = PANEL_SPECS[self.panel_type]
        current_count = self.tab_widget.count()
        if current_count >= spec["max_loops"]:
            self._info("loop_limit_title", "loop_limit_message", panel=self.panel_type, max_loops=spec["max_loops"])
            return

        loop_to_copy = None
        if copy_prompt and current_count > 0:
            options = [self.t("copy_none")]
            for i in range(current_count):
                options.append(self.t("copy_from", name=self.tab_widget.tabText(i)))
            
            # Create Custom Input Dialog for theme sync
            dialog = QInputDialog(self)
            dialog.setWindowTitle(self.t("new_loop_title"))
            dialog.setLabelText(self.t("choose_copy_loop"))
            dialog.setComboBoxItems(options)
            dialog.setComboBoxEditable(False)
            self._set_native_dark_title_bar(self.theme in ["dark", "industrial"], dialog)
            
            if dialog.exec() == QInputDialog.Accepted:
                item = dialog.textValue()
                if item != self.t("copy_none"):
                    try:
                        idx = options.index(item) - 1
                        loop_to_copy = self.tab_widget.widget(idx)
                    except (ValueError, IndexError):
                        pass

        loop = LoopEditorWidget(self.panel_type, self.product_db, self)
        if loop_state:
            loop.import_state(loop_state)
        elif loop_to_copy and isinstance(loop_to_copy, LoopEditorWidget):
            state = loop_to_copy.export_state()
            loop.import_state(state)
        else:
            loop.apply_panel_settings()

        index = self.tab_widget.addTab(loop, "")
        self._resync_tab_names()
        self.tab_widget.setCurrentWidget(loop)
        self._update_loop_label()
        loop.edit_aux.textChanged.connect(self._recalc_global_battery)
        loop.data_changed.connect(self._recalc_global_battery)
        loop.data_changed.connect(self._capture_current_workspace)
        loop.combo_addr_limit.currentIndexChanged.connect(
            lambda idx, src_loop=loop: self._sync_loop_addr_limit(src_loop, idx)
        )
        loop.edit_min_voltage.textChanged.connect(
            lambda value, src_loop=loop: self._sync_loop_min_voltage(src_loop, value)
        )
        self._inject_red_close_button(index)
        self._recalc_global_battery()
        self._capture_current_workspace()

    def _inject_red_close_button(self, index):
        button = QPushButton("×")
        button.setFixedSize(18, 18)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(self.close_tab_button_style())
        button.setContentsMargins(0, 0, 0, 0)
        button.clicked.connect(lambda: self._handle_manual_close(button))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, button)

    def _handle_manual_close(self, button):
        for index in range(self.tab_widget.count()):
            if self.tab_widget.tabBar().tabButton(index, QTabBar.RightSide) == button:
                self.tab_widget.tabCloseRequested.emit(index)
                break

    def _close_loop(self, index):
        if self.tab_widget.count() <= 1:
            self._info("notice_title", "close_loop_keep_one")
            return
        tab_name = self.tab_widget.tabText(index)
        if self._question("close_loop_title", "close_loop_message", tab_name=tab_name) == QMessageBox.Yes:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()
            self._resync_tab_names()
            self._update_loop_label()
            self._recalc_global_battery()
            self._refresh_close_buttons()
            self._update_add_button_pos()
            self._capture_current_workspace()

    def _inject_red_close_button(self, index):
        button = QPushButton("x")
        button.setFixedSize(18, 18)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(self.close_tab_button_style())
        button.setContentsMargins(0, 0, 0, 0)
        button.clicked.connect(lambda: self._handle_manual_close(button))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_add_button_pos()

    def _update_add_button_pos(self):
        if not hasattr(self, "btn_add_loop"):
            return
        self.btn_add_loop.setVisible(self.tab_widget.count() < PANEL_SPECS[self.panel_type]["max_loops"])
        total = self.tab_widget.count()
        current = self.tab_widget.currentIndex() + 1 if total else 0
        if total:
            self.lbl_loop_summary.setText(f"Loop workspace {current} of {total}")
        else:
            self.lbl_loop_summary.setText("No loop workspace loaded")
        self._update_page_header(self._get_active_nav_key())

    def _clear_current_panel_config(self):
        if self._question("clear_config_title", "clear_config_message") == QMessageBox.Yes:
            self.panel_workspace = self._default_workspace_state()
            self._load_workspace()

    def _recalc_global_battery(self):
        spec = PANEL_SPECS[self.panel_type]
        host_current = spec["quiescent"]
        total_aux = 0
        total_standby = 0
        total_alarm = 0
        loops = []
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loops.append(loop)
                total_aux += loop.get_aux_current()
                total_standby += loop.get_loop_standby_current()
                total_alarm += loop.get_loop_alarm_current()
        i_std = (host_current + total_aux + total_standby) / 1000.0
        i_alm = (host_current + total_aux + total_alarm) / 1000.0
        effective_cap = 7.2 / 1.25
        h_std = effective_cap / i_std if i_std > 0 else 0
        h_alm = effective_cap / i_alm if i_alm > 0 else 0
        for loop in loops:
            loop.update_battery_display(h_std, h_alm)
        self._capture_current_workspace()

    def reload_products(self, refresh_only=False):
        self.product_db.load()
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loop.refresh_products()
                loop.run_calculation()
        if not refresh_only:
            self._capture_current_workspace()





