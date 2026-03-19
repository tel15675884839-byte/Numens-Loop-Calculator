import json
import os
import re
import sys

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QDoubleValidator, QFont, QIcon, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


ADDRESS_LIMIT = 125
MAX_ALARM_LEDS = 10
MAX_CABLE_LENGTH = 1000
PRODUCT_DB_FILENAME = "products_db.json"
ADMIN_PASSWORD = "1"
MODULE_CATEGORY_ALIASES = {"Input Module", "Output Module", "Input/Output Module"}
MODULE_CATEGORY_NAME = "I/O Module"

CABLE_TYPES = [
    {"size": "1.0", "resistance": 18.1, "label": "1.0 mm²"},
    {"size": "1.5", "resistance": 12.1, "label": "1.5 mm²"},
    {"size": "2.5", "resistance": 7.41, "label": "2.5 mm²"},
    {"size": "4.0", "resistance": 4.61, "label": "4.0 mm²"},
]

PANEL_SPECS = {
    "6004": {"quiescent": 230, "aux_limit": 200, "max_loops": 2},
    "6002": {"quiescent": 200, "aux_limit": 200, "max_loops": 6},
}

LANGUAGE_OPTIONS = {
    "zh": "中文",
    "en": "English",
    "pt": "Português",
    "es": "Español",
    "ru": "Русский",
    "ar": "العربية",
}

THEME_OPTIONS = {
    "light": {"zh": "浅色", "en": "Light", "pt": "Claro", "es": "Claro", "ru": "Светлая", "ar": "فاتح"},
    "dark": {"zh": "深色", "en": "Dark", "pt": "Escuro", "es": "Oscuro", "ru": "Тёмная", "ar": "داكن"},
}

TR = {
    "app_title": {"zh": "Numens 回路计算器", "en": "Numens Loop Calculator"},
    "theme": {"zh": "主题", "en": "Theme"},
    "language": {"zh": "语言", "en": "Language"},
    "workspace_panel_label": {"zh": "主机型号: {panel}", "en": "Panel Model: {panel}"},
    "workspace_loop_count": {"zh": "回路: {count}/{max_loops}", "en": "Loops: {count}/{max_loops}"},
    "panel_selector_label": {"zh": "主机切换:", "en": "Panel:"},
    "loop_tab_name": {"zh": "回路 {index}", "en": "Loop {index}"},
    "system_parameters": {"zh": "1. 系统参数", "en": "1. System Parameters"},
    "device_list": {"zh": "2. 设备清单", "en": "2. Device List"},
    "calculation_results": {"zh": "3. 计算结果", "en": "3. Calculation Results"},
    "loop_device_count": {"zh": "回路设备数:", "en": "Loop Devices:"},
    "loop_current": {"zh": "回路电流(mA):", "en": "Loop Current (mA):"},
    "minimum_voltage": {"zh": "最低电压(V):", "en": "Minimum Voltage (V):"},
    "cable_spec": {"zh": "电缆规格:", "en": "Cable Size:"},
    "add_loop": {"zh": "+ 添加回路", "en": "+ Add Loop"},
    "clear_config": {"zh": "清除所有配置", "en": "Clear All Config"},
    "delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "database_manage": {"zh": "数据库管理", "en": "Manage Database"},
    "website_url": {"zh": "www.numens.com", "en": "www.numens.com"},
    "table_index": {"zh": "序号", "en": "No."},
    "table_device_name": {"zh": "设备名称", "en": "Device Name"},
    "table_alarm": {"zh": "报警(mA)", "en": "Alarm (mA)"},
    "table_lead_dist": {"zh": "距前节点(m)", "en": "From Prev. Node (m)"},
    "table_interval_dist": {"zh": "组内间距(m)", "en": "In-Group Spacing (m)"},
    "table_qty": {"zh": "数量", "en": "Qty"},
    "current_loop_status": {"zh": "当前回路状态:", "en": "Current Loop Status:"},
    "point_load": {"zh": "点数负载", "en": "Address Load"},
    "total_loop_current": {"zh": "回路总电流", "en": "Total Loop Current"},
    "end_voltage": {"zh": "末端最低电压", "en": "End Voltage"},
    "loop_length": {"zh": "回路累计线长", "en": "Accumulated Cable Length"},
    "safety_suggestions": {"zh": "安全优化建议:", "en": "Safety Optimization:"},
    "max_install_distance": {"zh": "极限施工距离", "en": "Max Install Distance"},
    "recommended_cable": {"zh": "推荐最小线径", "en": "Recommended Min Cable"},
    "battery_estimate": {"zh": "电池续航估算(7.2Ah):", "en": "Battery Runtime Estimate (7.2Ah):"},
    "aux_load": {"zh": "AUX负载电流", "en": "AUX Load Current"},
    "standby_runtime": {"zh": "待机续航时长", "en": "Standby Runtime"},
    "alarm_runtime": {"zh": "报警续航时长", "en": "Alarm Runtime"},
    "diag_ok": {"zh": "系统诊断: 回路配置正常", "en": "System Diagnosis: Loop configuration is normal"},
    "diag_error_header": {"zh": "系统诊断: 存在异常", "en": "System Diagnosis: Issues detected"},
    "diag_address_over": {"zh": "地址数({value})超出限制({limit})", "en": "Address count ({value}) exceeds limit ({limit})"},
    "diag_current_over": {"zh": "回路电流({value:.1f}mA)超载", "en": "Loop current ({value:.1f}mA) is overloaded"},
    "diag_voltage_low": {"zh": "末端电压({value:.2f}V)过低", "en": "End voltage ({value:.2f}V) is too low"},
    "diag_length_over": {"zh": "线路总长({value:.1f}m)过长", "en": "Total cable length ({value:.1f}m) is too long"},
    "aux_over_title": {"zh": "AUX电流超限", "en": "AUX Current Limit"},
    "aux_over_message": {"zh": "当前主机 AUX 24V 输出最大允许负载为 200mA，已自动重置。", "en": "The panel AUX 24V output allows a maximum load of 200mA. It has been reset automatically."},
    "qty_warning_title": {"zh": "超限提示", "en": "Limit Warning"},
    "qty_warning_message": {"zh": "总设备数({total})超过了回路限制({limit})。\n该项最大允许设置为: {max_allowed}", "en": "The total device count ({total}) exceeds the loop limit ({limit}).\nThe maximum allowed for this row is: {max_allowed}"},
    "total_devices_over_title": {"zh": "设备总数超限", "en": "Device Total Exceeded"},
    "total_devices_over_message": {"zh": "当前总设备数({total})超过了回路限制({limit})。", "en": "The current total device count ({total}) exceeds the loop limit ({limit})."},
    "add_failed_title": {"zh": "添加失败", "en": "Add Failed"},
    "add_failed_message": {"zh": "当前回路点数已达上限({limit})，无法继续添加。", "en": "The current loop has reached its address limit ({limit}) and cannot add more devices."},
    "loop_limit_title": {"zh": "回路上限", "en": "Loop Limit"},
    "loop_limit_message": {"zh": "{panel} 主机最多支持 {max_loops} 个回路。", "en": "Panel {panel} supports up to {max_loops} loops."},
    "new_loop_title": {"zh": "新建回路", "en": "New Loop"},
    "new_loop_message": {"zh": "沿用当前回路的基础设置吗？", "en": "Reuse the current loop's base settings?"},
    "notice_title": {"zh": "提示", "en": "Notice"},
    "close_loop_keep_one": {"zh": "至少需要保留一个回路。", "en": "At least one loop must remain."},
    "close_loop_title": {"zh": "关闭回路", "en": "Close Loop"},
    "close_loop_message": {"zh": "确定要关闭 {tab_name} 吗？\n该回路的所有配置数据将丢失。", "en": "Close {tab_name}?\nAll configuration data in this loop will be lost."},
    "clear_config_title": {"zh": "清除所有配置", "en": "Clear All Config"},
    "clear_config_message": {"zh": "确定要清除 {panel} 的全部配置吗？\n当前主机下的所有回路和设备数据将被清空。", "en": "Clear all configuration for {panel}?\nAll loop and device data under this panel will be removed."},
    "yes": {"zh": "是", "en": "Yes"},
    "no": {"zh": "否", "en": "No"},
    "confirm": {"zh": "确定", "en": "OK"},
    "add_category_prefix": {"zh": " {category}", "en": " {category}"},
    "admin_password_title": {"zh": "管理员验证", "en": "Admin Verification"},
    "admin_password_label": {"zh": "请输入管理员密码：", "en": "Enter admin password:"},
    "admin_password_error": {"zh": "密码错误。", "en": "Incorrect password."},
    "admin_categories": {"zh": "类别", "en": "Categories"},
    "admin_products": {"zh": "产品", "en": "Products"},
    "admin_add_category": {"zh": "新增类别", "en": "Add Category"},
    "admin_rename_category": {"zh": "重命名类别", "en": "Rename Category"},
    "admin_delete_category": {"zh": "删除类别", "en": "Delete Category"},
    "admin_add_product": {"zh": "新增产品", "en": "Add Product"},
    "admin_delete_product": {"zh": "删除产品", "en": "Delete Product"},
    "admin_save": {"zh": "保存", "en": "Save"},
    "admin_close": {"zh": "关闭", "en": "Close"},
    "admin_enter_category": {"zh": "输入类别名称：", "en": "Enter category name:"},
    "admin_category_in_use": {"zh": "该类别下仍有产品，请先删除或移动产品。", "en": "This category still has products. Delete or move them first."},
    "admin_save_success": {"zh": "产品数据库已保存。", "en": "Product database saved."},
    "product_factory_name": {"zh": "工厂型号", "en": "Factory Name"},
    "product_customer_name": {"zh": "客户型号", "en": "Customer Name"},
    "product_category": {"zh": "类别", "en": "Category"},
    "product_standby": {"zh": "监视电流", "en": "Standby"},
    "product_alarm": {"zh": "报警电流", "en": "Alarm"},
    "product_led_cost": {"zh": "LED占位", "en": "LED Cost"},
    "product_type": {"zh": "类型", "en": "Type"},
}


def tr_text(lang, key, **kwargs):
    text = TR.get(key, {}).get(lang) or TR.get(key, {}).get("en") or key
    return text.format(**kwargs) if kwargs else text


def palette(theme):
    if theme == "dark":
        return {
            "window": "#12161c",
            "surface": "#1b222c",
            "surface_alt": "#232c38",
            "surface_soft": "#202833",
            "border": "#334052",
            "text": "#e6edf5",
            "muted": "#9fb0c4",
            "accent": "#58a6ff",
            "accent_soft": "#1c3958",
            "danger": "#ff7b72",
            "danger_soft": "#4a2525",
            "success": "#7ee787",
            "success_soft": "#1f3a28",
            "hover": "#263243",
        }
    return {
        "window": "#f0f2f5",
        "surface": "#ffffff",
        "surface_alt": "#f5f7fa",
        "surface_soft": "#f8f9fa",
        "border": "#dcdfe6",
        "text": "#303133",
        "muted": "#909399",
        "accent": "#409eff",
        "accent_soft": "#ecf5ff",
        "danger": "#f56c6c",
        "danger_soft": "#fef0f0",
        "success": "#67c23a",
        "success_soft": "#f0f9eb",
        "hover": "#ebf5ff",
    }


def app_style(theme):
    p = palette(theme)
    combo_arrow = "assets/combo-down-dark.svg" if theme == "dark" else "assets/combo-down.svg"
    spin_up = "assets/spin-up-dark.svg" if theme == "dark" else "assets/spin-up.svg"
    spin_down = "assets/spin-down-dark.svg" if theme == "dark" else "assets/spin-down.svg"
    return f"""
QMainWindow {{ background-color: {p['window']}; }}
QWidget {{ color: {p['text']}; }}
QGroupBox {{ font-weight: bold; border: 1px solid {p['border']}; border-radius: 8px; margin-top: 16px; padding: 12px; background-color: {p['surface']}; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 10px; top: 4px; color: {p['accent']}; padding: 0 4px; }}
QTableWidget {{ border: 1px solid {p['border']}; gridline-color: {p['border']}; background-color: {p['surface']}; alternate-background-color: {p['surface_alt']}; selection-background-color: {p['accent_soft']}; selection-color: {p['text']}; }}
QHeaderView::section {{ background-color: {p['surface_alt']}; color: {p['text']}; border: none; border-bottom: 1px solid {p['border']}; border-right: 1px solid {p['border']}; padding: 4px; font-weight: bold; }}
QLineEdit, QComboBox, QSpinBox {{ height: 26px; border: 1px solid {p['border']}; border-radius: 4px; padding: 0 5px; background: {p['surface']}; color: {p['text']}; }}
QComboBox {{ padding-right: 22px; }}
QComboBox QAbstractItemView, QAbstractItemView {{ background: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']}; selection-background-color: {p['accent_soft']}; selection-color: {p['text']}; outline: none; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid {p['border']}; background: {p['surface']}; border-top-right-radius: 4px; border-bottom-right-radius: 4px; }}
QComboBox::down-arrow {{ image: url({combo_arrow}); width: 8px; height: 5px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; border-left: 1px solid {p['border']}; background: {p['surface']}; }}
QSpinBox::up-arrow {{ image: url({spin_up}); width: 8px; height: 5px; }}
QSpinBox::down-arrow {{ image: url({spin_down}); width: 8px; height: 5px; }}
#resCard, #suggestCard {{ background-color: {p['surface_soft']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 6px 10px; }}
#resName, #suggestName {{ color: {p['text']}; font-size: 13px; font-weight: 500; }}
#resVal, #suggestVal {{ font-weight: bold; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; font-size: 16px; color: {p['text']}; }}
#resUnit {{ color: {p['muted']}; font-size: 11px; font-weight: bold; padding-left: 2px; }}
"""


class NumericDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        validator = QDoubleValidator(0.0, 9999.0, 2, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        return editor


def set_message_box_texts(box, owner):
    for role, key in [(QMessageBox.Yes, "yes"), (QMessageBox.No, "no"), (QMessageBox.Ok, "confirm")]:
        button = box.button(role)
        if button:
            button.setText(owner.t(key))


class ProductDatabase:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, PRODUCT_DB_FILENAME)
        self.products = []
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self._migrate_from_legacy()
        with open(self.path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        self.products = [self._normalize_product(dict(product)) for product in data.get("products", [])]
        self._merged_options = self._build_merged_options()
        self.save()

    def _normalize_product(self, product):
        if product.get("category") in MODULE_CATEGORY_ALIASES:
            product["category"] = MODULE_CATEGORY_NAME
        if product.get("type") in MODULE_CATEGORY_ALIASES:
            product["type"] = MODULE_CATEGORY_NAME
        return product

    def _migrate_from_legacy(self):
        legacy_path = os.path.join(self.base_dir, "devices_new.json")
        products = []
        if os.path.exists(legacy_path):
            with open(legacy_path, "r", encoding="utf-8-sig") as f:
                legacy = json.load(f)
            for index, item in enumerate(legacy, start=1):
                name = item.get("name", f"Product {index}")
                category = item.get("type", "Other")
                products.append(
                    self._normalize_product(
                        {
                        "id": f"product-{index:04d}",
                        "category": category,
                        "factory_name": name,
                        "customer_name": name,
                        "standby": float(item.get("standby", 0.5)),
                        "alarm": float(item.get("alarm", 2.0)),
                        "ledCost": int(item.get("ledCost", 1)),
                        "type": category,
                        }
                    )
                )
        else:
            products = [
                self._normalize_product(
                    {
                    "id": "product-0001",
                    "category": "Detector",
                    "factory_name": "Generic Device",
                    "customer_name": "Generic Device",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                    "type": "Detector",
                    }
                )
            ]
        self.products = products
        self.save()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"products": self.products}, f, ensure_ascii=False, indent=2)

    def categories(self):
        seen = []
        for product in self.products:
            category = product.get("category", "Other")
            if category not in seen:
                seen.append(category)
        return seen

    def products_by_category(self, category):
        return [dict(product) for product in self.products if product.get("category") == category]

    def product_options_by_category(self, category):
        return [self._product_to_option(product) for product in self.products if product.get("category") == category]

    def merged_options_by_category(self, category):
        return [dict(option) for option in self._merged_options.get(category, [])]

    def get_merged_option(self, merge_key):
        for options in self._merged_options.values():
            for option in options:
                if option.get("merge_key") == merge_key:
                    return dict(option)
        return None

    def resolve_row_state(self, row_state):
        state = dict(row_state or {})
        product_id = state.get("product_id")
        if product_id:
            option = self.get_product_option(product_id)
            if option:
                return {**option, **state}
        merge_key = state.get("merge_key")
        if merge_key:
            option = self.get_merged_option(merge_key)
            if option:
                member_ids = option.get("member_product_ids", [])
                if member_ids:
                    product_option = self.get_product_option(member_ids[0])
                    if product_option:
                        state.pop("merge_key", None)
                        state.pop("member_product_ids", None)
                        return {**product_option, **state}
        legacy_product_id = state.get("product_id")
        if legacy_product_id:
            option = self.get_merged_option_for_product(legacy_product_id)
            if option:
                member_ids = option.get("member_product_ids", [])
                if member_ids:
                    product_option = self.get_product_option(member_ids[0])
                    if product_option:
                        state.pop("merge_key", None)
                        state.pop("member_product_ids", None)
                        return {**product_option, **state}
        return state

    def get_merged_option_for_product(self, product_id):
        for options in self._merged_options.values():
            for option in options:
                if product_id in option.get("member_product_ids", []):
                    return dict(option)
        return None

    def get_product(self, product_id):
        for product in self.products:
            if product.get("id") == product_id:
                return dict(product)
        return None

    def get_product_option(self, product_id):
        product = self.get_product(product_id)
        return self._product_to_option(product) if product else None

    def update_customer_name(self, product_id, customer_name):
        customer_name = (customer_name or "").strip()
        if not customer_name:
            return None
        for product in self.products:
            if product.get("id") == product_id:
                product["customer_name"] = customer_name
                self.save()
                return dict(product)
        return None

    def replace_all(self, products):
        self.products = [self._normalize_product(dict(product)) for product in products]
        self._merged_options = self._build_merged_options()
        self.save()

    def _product_to_option(self, product):
        if not product:
            return None
        customer_name = str(product.get("customer_name", "")).strip()
        product_name = str(product.get("product_name", "")).strip()
        popup_name = f"{customer_name} - {product_name}" if customer_name and product_name else (product_name or customer_name)
        display_name = product_name or customer_name
        return {
            "product_id": product.get("id"),
            "category": product.get("category", "Other"),
            "type": product.get("type", product.get("category", "Other")),
            "standby": float(product.get("standby", 0.5)),
            "alarm": float(product.get("alarm", 0.0)),
            "ledCost": int(product.get("ledCost", 1)),
            "customer_name": customer_name,
            "factory_name": str(product.get("factory_name", "")).strip(),
            "product_name": product_name,
            "popup_name": popup_name,
            "display_name": display_name,
        }

    def next_product_id(self):
        values = []
        for product in self.products:
            pid = product.get("id", "")
            if pid.startswith("product-"):
                try:
                    values.append(int(pid.split("-")[-1]))
                except ValueError:
                    pass
        return f"product-{(max(values) + 1 if values else 1):04d}"

    def _merge_key(self, product):
        return "|".join(
            [
                str(product.get("standby", 0)),
                str(product.get("alarm", 0)),
                str(product.get("ledCost", 1)),
                str(product.get("type", "")),
            ]
        )

    def _build_merged_options(self):
        grouped = {}
        category_order = []
        for product in self.products:
            category = product.get("category", "Other")
            if category not in category_order:
                category_order.append(category)
            group_key = (category, self._merge_key(product))
            grouped.setdefault(group_key, []).append(dict(product))

        merged = {category: [] for category in category_order}
        for (category, merge_key), members in grouped.items():
            members = sorted(members, key=lambda item: item.get("factory_name", ""))
            first = members[0]
            merged[category].append(
                {
                    "merge_key": merge_key,
                    "category": category,
                    "type": first.get("type", category),
                    "standby": float(first.get("standby", 0.5)),
                    "alarm": float(first.get("alarm", 0.0)),
                    "ledCost": int(first.get("ledCost", 1)),
                    "member_product_ids": [item.get("id") for item in members if item.get("id")],
                    "display_name": self._build_display_name([item.get("factory_name", "") for item in members]),
                }
            )
        return merged

    def _build_display_name(self, names):
        clean = [name for name in names if name]
        if not clean:
            return ""
        if len(clean) == 1:
            return clean[0]
        parsed = [self._split_model_name(name) for name in clean]
        if all(part is not None for part in parsed):
            prefixes = {part[0] for part in parsed}
            suffixes = {part[2] for part in parsed}
            numbers = sorted(part[1] for part in parsed)
            if len(prefixes) == 1 and len(suffixes) == 1:
                prefix = parsed[0][0]
                suffix = parsed[0][2]
                if len(numbers) <= 3:
                    return f"{prefix}{'/'.join(numbers)}{suffix}"
                return f"{prefix}{numbers[0]}...{numbers[-1]}{suffix}"
        if len(clean) <= 3:
            return "/".join(clean)
        return f"{clean[0]}...{clean[-1]}"

    def _split_model_name(self, name):
        match = re.match(r"^(.*?)(\d+)([^0-9]*)$", name)
        if not match:
            return None
        return match.group(1), match.group(2), match.group(3)


class ProductComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setFrame(False)
        self.currentIndexChanged.connect(self._refresh_closed_text)

    def add_product_option(self, option):
        popup_name = option.get("popup_name", "")
        self.addItem(popup_name, option.get("product_id"))
        self.setItemData(self.count() - 1, option.get("display_name", ""), Qt.UserRole + 1)
        self.setItemData(self.count() - 1, dict(option), Qt.UserRole + 2)

    def _refresh_closed_text(self):
        self.lineEdit().setText(self.currentData(Qt.UserRole + 1) or "")


class ProductDatabaseDialog(QDialog):
    def __init__(self, main_app, product_db, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.product_db = product_db
        self.working_products = [dict(product) for product in product_db.products]
        self.visible_category = None
        self.setMinimumSize(980, 620)
        self._build_ui()
        self._load_categories()
        self.retranslate_ui()
        self.refresh_theme()

    def t(self, key, **kwargs):
        return self.main_app.t(key, **kwargs)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(0)

        left_panel = QWidget()
        left_panel.setFixedWidth(100)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        self.lbl_categories = QLabel()
        left_layout.addWidget(self.lbl_categories)
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(100)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_list, 1)
        left_buttons = QVBoxLayout()
        left_buttons.setContentsMargins(0, 0, 0, 0)
        left_buttons.setSpacing(4)
        self.btn_add_category = QPushButton()
        self.btn_rename_category = QPushButton()
        self.btn_delete_category = QPushButton()
        left_buttons.addWidget(self.btn_add_category)
        left_buttons.addWidget(self.btn_rename_category)
        left_buttons.addWidget(self.btn_delete_category)
        left_layout.addLayout(left_buttons)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.lbl_products = QLabel()
        right_layout.addWidget(self.lbl_products)
        self.product_table = QTableWidget(0, 5)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.product_table.setColumnWidth(0, 170)
        self.product_table.setColumnWidth(1, 170)
        self.product_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.product_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.product_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        right_layout.addWidget(self.product_table, 1)
        button_row = QHBoxLayout()
        self.btn_add_product = QPushButton()
        self.btn_delete_product = QPushButton()
        self.btn_save = QPushButton()
        self.btn_close = QPushButton()
        button_row.addWidget(self.btn_add_product)
        button_row.addWidget(self.btn_delete_product)
        button_row.addStretch()
        button_row.addWidget(self.btn_save)
        button_row.addWidget(self.btn_close)
        right_layout.addLayout(button_row)

        layout.addWidget(left_panel, 0)
        layout.addLayout(right_layout, 1)

        self.btn_add_category.clicked.connect(self._add_category)
        self.btn_rename_category.clicked.connect(self._rename_category)
        self.btn_delete_category.clicked.connect(self._delete_category)
        self.btn_add_product.clicked.connect(self._add_product)
        self.btn_delete_product.clicked.connect(self._delete_product)
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self.reject)

    def retranslate_ui(self):
        self.setWindowTitle(self.t("database_manage"))
        self.lbl_categories.setText(self.t("admin_categories"))
        self.lbl_products.setText(self.t("admin_products"))
        self.btn_add_category.setText(self.t("admin_add_category"))
        self.btn_rename_category.setText(self.t("admin_rename_category"))
        self.btn_delete_category.setText(self.t("admin_delete_category"))
        self.btn_add_product.setText(self.t("admin_add_product"))
        self.btn_delete_product.setText(self.t("admin_delete_product"))
        self.btn_save.setText(self.t("admin_save"))
        self.btn_close.setText(self.t("admin_close"))
        self.product_table.setHorizontalHeaderLabels(
            [
                self.t("product_factory_name"),
                self.t("product_customer_name"),
                self.t("product_name"),
                self.t("product_standby"),
                self.t("product_alarm"),
            ]
        )

    def refresh_theme(self):
        self.btn_add_category.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_rename_category.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_delete_category.setStyleSheet(self.main_app.danger_outline_button_style())
        self.btn_add_product.setStyleSheet(self.main_app.primary_button_style())
        self.btn_delete_product.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_save.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_close.setStyleSheet(self.main_app.secondary_button_style())

    def _categories(self):
        seen = []
        for product in self.working_products:
            category = product.get("category", "Other")
            if category not in seen:
                seen.append(category)
        return seen

    def _load_categories(self):
        self.category_list.clear()
        for category in self._categories():
            self.category_list.addItem(category)
        if self.category_list.count():
            self.category_list.setCurrentRow(0)
        else:
            self.product_table.setRowCount(0)

    def _current_category(self):
        item = self.category_list.currentItem()
        return item.text() if item else None

    def _reload_products(self):
        category = self._current_category()
        self.visible_category = category
        rows = [product for product in self.working_products if product.get("category") == category] if category else []
        self.product_table.setRowCount(0)
        for row, product in enumerate(rows):
            self.product_table.insertRow(row)
            values = [
                product.get("factory_name", ""),
                product.get("customer_name", ""),
                product.get("product_name", ""),
                str(product.get("standby", 0)),
                str(product.get("alarm", 0)),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, product.get("id"))
                self.product_table.setItem(row, col, item)

    def _flush_visible_products(self):
        visible = self._collect_table_products()
        if not visible:
            return
        self.working_products = [visible.get(product["id"], product) for product in self.working_products]

    def _on_category_changed(self):
        self._flush_visible_products()
        self._reload_products()

    def _ask_text(self, title_key, label_key, text=""):
        value, ok = QInputDialog.getText(self, self.t(title_key), self.t(label_key), text=text)
        return value.strip(), ok

    def _add_category(self):
        name, ok = self._ask_text("admin_add_category", "admin_enter_category")
        if ok and name and name not in self._categories():
            self.category_list.addItem(name)
            self.category_list.setCurrentRow(self.category_list.count() - 1)

    def _rename_category(self):
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        name, ok = self._ask_text("admin_rename_category", "admin_enter_category", category)
        if ok and name and name != category:
            for product in self.working_products:
                if product.get("category") == category:
                    product["category"] = name
                    if product.get("type") == category:
                        product["type"] = name
            self._load_categories()
            items = self.category_list.findItems(name, Qt.MatchExactly)
            if items:
                self.category_list.setCurrentItem(items[0])

    def _delete_category(self):
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        if any(product.get("category") == category for product in self.working_products):
            QMessageBox.warning(self, self.t("notice_title"), self.t("admin_category_in_use"))
            return
        self.category_list.takeItem(self.category_list.currentRow())

    def _add_product(self):
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        product = {
            "id": self.product_db.next_product_id(),
            "category": category,
            "factory_name": "New Product",
            "customer_name": "New Product",
            "product_name": "",
            "standby": 0.5,
            "alarm": 2.0,
            "ledCost": 1,
            "type": category,
        }
        self.working_products.append(product)
        self._reload_products()
        if self.product_table.rowCount():
            self.product_table.selectRow(self.product_table.rowCount() - 1)

    def _delete_product(self):
        self._flush_visible_products()
        row = self.product_table.currentRow()
        if row < 0:
            return
        item = self.product_table.item(row, 0)
        product_id = item.data(Qt.UserRole) if item else None
        self.working_products = [product for product in self.working_products if product.get("id") != product_id]
        self._reload_products()

    def _collect_table_products(self):
        category = self.visible_category
        collected = {}
        for row in range(self.product_table.rowCount()):
            first = self.product_table.item(row, 0)
            if not first:
                continue
            product_id = first.data(Qt.UserRole)
            collected[product_id] = {
                "id": product_id,
                "factory_name": self.product_table.item(row, 0).text().strip(),
                "customer_name": self.product_table.item(row, 1).text().strip(),
                "product_name": self.product_table.item(row, 2).text().strip(),
                "category": next((product.get("category", category or "Other") for product in self.working_products if product.get("id") == product_id), category or "Other"),
                "standby": float(self.product_table.item(row, 3).text() or 0),
                "alarm": float(self.product_table.item(row, 4).text() or 0),
                "ledCost": next((product.get("ledCost", 1) for product in self.working_products if product.get("id") == product_id), 1),
                "type": next((product.get("type", category or "Other") for product in self.working_products if product.get("id") == product_id), category or "Other"),
            }
        return collected

    def _save(self):
        self._flush_visible_products()
        updated_visible = self._collect_table_products()
        merged = []
        for product in self.working_products:
            merged.append(updated_visible.get(product["id"], product))
        self.product_db.replace_all(merged)
        self.main_app.reload_products()
        QMessageBox.information(self, self.t("notice_title"), self.t("admin_save_success"))
        self.accept()


class LoopEditorWidget(QWidget):
    data_changed = Signal()

    def __init__(self, panel_type, product_db, main_app=None):
        super().__init__(main_app)
        self.panel_type = panel_type
        self.product_db = product_db
        self.main_app = main_app
        self.results = {}
        self.units = {}
        self.result_labels = {}
        self.result_keys = {}
        self.last_errors = []
        self.category_buttons = []
        self._init_ui()
        self._bind()
        self.apply_panel_settings()
        self.retranslate_ui()
        self.refresh_theme()

    def t(self, key, **kwargs):
        return self.main_app.t(key, **kwargs)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        self.sys_group = QGroupBox()
        sys_layout = QHBoxLayout(self.sys_group)
        sys_layout.setContentsMargins(10, 18, 10, 10)
        sys_layout.setSpacing(5)

        self.lbl_addr_limit = QLabel()
        self.combo_addr_limit = QComboBox()
        self.combo_addr_limit.addItems(["125", "250"])
        self.combo_addr_limit.setFixedWidth(70)
        self.lbl_max_current = QLabel()
        self.edit_max_current = QLineEdit("400")
        self.edit_max_current.setFixedWidth(50)
        self.edit_max_current.setEnabled(False)
        self.lbl_min_voltage = QLabel()
        self.edit_min_voltage = QLineEdit("17")
        self.edit_min_voltage.setFixedWidth(50)
        self.edit_min_voltage.setValidator(QDoubleValidator(0.0, 30.0, 1))
        self.lbl_cable = QLabel()
        self.combo_cable = QComboBox()
        self.combo_cable.setMinimumWidth(180)

        for label, widget in [
            (self.lbl_addr_limit, self.combo_addr_limit),
            (self.lbl_max_current, self.edit_max_current),
            (self.lbl_min_voltage, self.edit_min_voltage),
            (self.lbl_cable, self.combo_cable),
        ]:
            sys_layout.addWidget(label)
            sys_layout.addWidget(widget)
            sys_layout.addSpacing(20)
        self.btn_add_loop_inline = QPushButton()
        self.btn_add_loop_inline.clicked.connect(lambda: self.main_app._add_loop())
        self.btn_clear_config_inline = QPushButton()
        self.btn_clear_config_inline.clicked.connect(self.main_app._clear_current_panel_config)
        sys_layout.addWidget(self.btn_add_loop_inline)
        sys_layout.addWidget(self.btn_clear_config_inline)
        sys_layout.addSpacing(12)
        sys_layout.addStretch()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            self.logo_label.setPixmap(QPixmap(logo_path).scaledToWidth(220, Qt.SmoothTransformation))
        sys_layout.addWidget(self.logo_label)
        main_layout.addWidget(self.sys_group)

        work_area = QHBoxLayout()
        work_area.setSpacing(15)

        self.dev_group = QGroupBox()
        dev_layout = QVBoxLayout(self.dev_group)
        dev_layout.setContentsMargins(10, 15, 10, 10)
        toolbar = QHBoxLayout()
        self.category_toolbar = QHBoxLayout()
        self.category_toolbar.setSpacing(8)
        toolbar.addLayout(self.category_toolbar)
        toolbar.addStretch()
        self.btn_manage_db = QPushButton()
        self.btn_delete = QPushButton()
        toolbar.addWidget(self.btn_manage_db)
        toolbar.addWidget(self.btn_delete)
        dev_layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 70)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegateForColumn(2, NumericDelegate())
        self.table.setItemDelegateForColumn(3, NumericDelegate())
        self.table.setItemDelegateForColumn(4, NumericDelegate())
        self.table.verticalHeader().setVisible(False)
        dev_layout.addWidget(self.table)
        work_area.addWidget(self.dev_group, 7)

        self.res_group = QGroupBox()
        res_layout = QVBoxLayout(self.res_group)
        res_layout.setContentsMargins(8, 15, 8, 10)
        res_layout.setSpacing(4)
        self.status_label = QLabel()
        res_layout.addWidget(self.status_label)
        self._make_result(res_layout, "addr", "point_load", f"/{ADDRESS_LIMIT}", "resCard", "0")
        self._make_result(res_layout, "curr", "total_loop_current", "mA", "resCard", "0")
        self._make_result(res_layout, "volt", "end_voltage", "V", "resCard", "0")
        self._make_result(res_layout, "lens", "loop_length", "m", "resCard", "0")
        res_layout.addSpacing(5)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        res_layout.addWidget(divider)
        res_layout.addSpacing(5)
        self.opt_label = QLabel()
        res_layout.addWidget(self.opt_label)
        self._make_result(res_layout, "max_len", "max_install_distance", "m", "suggestCard", "0")
        self._make_result(res_layout, "rec_cable", "recommended_cable", "", "suggestCard", "0")
        res_layout.addSpacing(5)
        self.batt_label = QLabel()
        res_layout.addWidget(self.batt_label)
        aux_card = QFrame()
        aux_card.setObjectName("suggestCard")
        aux_row = QHBoxLayout(aux_card)
        aux_row.setContentsMargins(8, 2, 8, 2)
        self.aux_name = QLabel()
        self.aux_name.setObjectName("suggestName")
        self.edit_aux = QLineEdit("0")
        self.edit_aux.setFixedWidth(55)
        self.edit_aux.setAlignment(Qt.AlignRight)
        self.edit_aux.setValidator(QIntValidator(0, 9999))
        self.aux_unit = QLabel("mA")
        self.aux_unit.setObjectName("resUnit")
        aux_row.addWidget(self.aux_name)
        aux_row.addStretch()
        aux_row.addWidget(self.edit_aux)
        aux_row.addWidget(self.aux_unit)
        res_layout.addWidget(aux_card)
        self._make_result(res_layout, "std_time", "standby_runtime", "h", "suggestCard", "---")
        self._make_result(res_layout, "alm_time", "alarm_runtime", "h", "suggestCard", "---")
        res_layout.addSpacing(10)
        self.diag_panel = QLabel()
        self.diag_panel.setWordWrap(True)
        self.diag_panel.setAlignment(Qt.AlignCenter)
        res_layout.addWidget(self.diag_panel)
        res_layout.addStretch()
        self.website_label = QLabel()
        self.website_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.website_label.setCursor(Qt.PointingHandCursor)
        self.website_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.website_label.setOpenExternalLinks(False)
        self.website_label.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        res_layout.addWidget(self.website_label)
        work_area.addWidget(self.res_group, 3)

        main_layout.addLayout(work_area)

    def _make_result(self, layout, key, label_key, unit, card_name, default_value="0"):
        card = QFrame()
        card.setObjectName(card_name)
        row = QHBoxLayout(card)
        row.setContentsMargins(8, 4, 8, 4)
        name = QLabel()
        name.setObjectName("suggestName" if card_name == "suggestCard" else "resName")
        value = QLabel(default_value)
        value.setObjectName("suggestVal" if card_name == "suggestCard" else "resVal")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        unit_label = QLabel(unit)
        unit_label.setObjectName("resUnit")
        row.addWidget(name)
        row.addStretch()
        row.addWidget(value)
        row.addWidget(unit_label)
        layout.addWidget(card)
        self.results[key] = value
        self.units[key] = unit_label
        self.result_labels[key] = name
        self.result_keys[key] = label_key

    def _bind(self):
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_manage_db.clicked.connect(self.open_database_manager)
        self.table.itemChanged.connect(self.on_table_changed)
        self.combo_cable.currentIndexChanged.connect(self.run_calculation)
        self.edit_min_voltage.textChanged.connect(self.run_calculation)
        self.edit_aux.textChanged.connect(self.run_calculation)
        self.edit_aux.editingFinished.connect(self._validate_aux_curr)
        self.combo_addr_limit.currentIndexChanged.connect(self.validate_all_quantities)
        self.combo_addr_limit.currentIndexChanged.connect(self.run_calculation)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild_category_buttons(self):
        self._clear_layout(self.category_toolbar)
        self.category_buttons = []
        for category in self.product_db.categories():
            button = QPushButton(self.t("add_category_prefix", category=category))
            button.clicked.connect(lambda checked=False, cat=category: self.add_device_row(cat))
            self.category_toolbar.addWidget(button)
            self.category_buttons.append(button)

    def retranslate_ui(self):
        self.sys_group.setTitle(self.t("system_parameters"))
        self.dev_group.setTitle(self.t("device_list"))
        self.res_group.setTitle(self.t("calculation_results"))
        self.lbl_addr_limit.setText(self.t("loop_device_count"))
        self.lbl_max_current.setText(self.t("loop_current"))
        self.lbl_min_voltage.setText(self.t("minimum_voltage"))
        self.lbl_cable.setText(self.t("cable_spec"))
        self.btn_add_loop_inline.setText(self.t("add_loop"))
        self.btn_clear_config_inline.setText(self.t("clear_config"))
        self.btn_manage_db.setText(self.t("database_manage"))
        self.btn_delete.setText(self.t("delete_selected"))
        website = self.t("website_url")
        self.website_label.setText(f"<a href='https://{website}'>{website}</a>")
        self.website_label.setToolTip(f"https://{website}")
        self.table.setHorizontalHeaderLabels(
            [
                self.t("table_index"),
                self.t("table_device_name"),
                self.t("table_alarm"),
                self.t("table_lead_dist"),
                self.t("table_interval_dist"),
                self.t("table_qty"),
            ]
        )
        self.status_label.setText(self.t("current_loop_status"))
        self.opt_label.setText(self.t("safety_suggestions"))
        self.batt_label.setText(self.t("battery_estimate"))
        self.aux_name.setText(self.t("aux_load"))
        for key, label_key in self.result_keys.items():
            self.result_labels[key].setText(self.t(label_key))
        self._reload_cables()
        self._rebuild_category_buttons()
        self.update_diag_panel(self.last_errors)

    def refresh_theme(self):
        muted = self.main_app.p["muted"]
        self.btn_add_loop_inline.setStyleSheet(self.main_app.colored_outline_button_style(self.main_app.p["accent"]))
        self.btn_clear_config_inline.setStyleSheet(self.main_app.colored_outline_button_style(self.main_app.p["danger"]))
        self.btn_manage_db.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_delete.setStyleSheet(self.main_app.secondary_button_style())
        for button in self.category_buttons:
            button.setStyleSheet(self.main_app.primary_button_style())
        self.edit_aux.setStyleSheet(self.main_app.inline_input_style())
        for label in [self.status_label, self.opt_label, self.batt_label]:
            label.setStyleSheet(f"color: {muted}; font-weight: bold; font-size: 11px;")
        self.website_label.setStyleSheet(
            f"QLabel {{ color: {self.main_app.p['danger']}; font-weight: bold; font-size: 13px; padding-top: 8px; }}"
            f"QLabel:hover {{ color: {self.main_app.p['accent']}; }}"
        )
        self._refresh_interval_backgrounds()
        self.update_diag_panel(self.last_errors)

    def _reload_cables(self):
        current = self.combo_cable.currentData()
        current_size = current["size"] if current else None
        self.combo_cable.blockSignals(True)
        self.combo_cable.clear()
        for cable in CABLE_TYPES:
            self.combo_cable.addItem(f"{cable['label']} ({cable['resistance']}Ω/km)", cable)
            if cable["size"] == current_size:
                self.combo_cable.setCurrentIndex(self.combo_cable.count() - 1)
        if self.combo_cable.currentIndex() < 0 and self.combo_cable.count() > 1:
            self.combo_cable.setCurrentIndex(1)
        self.combo_cable.blockSignals(False)

    def apply_panel_settings(self):
        self.edit_max_current.setText("400")
        if self.panel_type == "6004":
            self.combo_addr_limit.setCurrentIndex(0)
            self.combo_addr_limit.setEnabled(False)
        else:
            self.combo_addr_limit.setEnabled(True)
        self.validate_all_quantities()
        self.run_calculation()

    def _warn(self, title_key, msg_key, **kwargs):
        box = QMessageBox(QMessageBox.Warning, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        box.setStandardButtons(QMessageBox.Ok)
        set_message_box_texts(box, self)
        box.exec()

    def _validate_aux_curr(self):
        try:
            if int(self.edit_aux.text() or 0) > 200:
                self._warn("aux_over_title", "aux_over_message")
                self.edit_aux.setText("200")
                self.run_calculation()
        except Exception:
            pass

    def validate_all_quantities(self):
        limit = int(self.combo_addr_limit.currentText())
        total = self.get_total_qty()
        if total > limit:
            self._warn("total_devices_over_title", "total_devices_over_message", total=total, limit=limit)

    def get_total_qty(self):
        total = 0
        for row in range(self.table.rowCount()):
            spin = self.table.cellWidget(row, 5)
            if isinstance(spin, QSpinBox):
                total += spin.value()
        return total

    def _default_row_snapshot(self, category):
        options = self.product_db.product_options_by_category(category)
        if options:
            option = options[0]
            return {
                "product_id": option["product_id"],
                "display_name": option["display_name"],
                "category": option["category"],
                "standby": option["standby"],
                "alarm": option["alarm"],
                "ledCost": option["ledCost"],
                "type": option["type"],
                "customer_name": option["customer_name"],
                "factory_name": option["factory_name"],
                "product_name": option["product_name"],
                "lead_dist": "10.0" if self.table.rowCount() > 0 else "0.0",
                "interval_dist": "10.0",
                "qty": 1,
            }
        return {
            "product_id": None,
            "display_name": "",
            "category": category,
            "standby": 0.5,
            "alarm": 0.0,
            "ledCost": 1,
            "type": category,
            "lead_dist": "10.0" if self.table.rowCount() > 0 else "0.0",
            "interval_dist": "10.0",
            "qty": 1,
        }

    def _create_product_combo(self, category, selected_key=None, current_text=None):
        combo = ProductComboBox()
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMinimumContentsLength(42)
        combo.view().setMinimumWidth(560)
        for option in self.product_db.product_options_by_category(category):
            combo.add_product_option(option)
        if selected_key:
            index = combo.findData(selected_key)
            if index >= 0:
                combo.setCurrentIndex(index)
        if current_text:
            index = combo.findText(current_text)
            if index < 0:
                for i in range(combo.count()):
                    if combo.itemData(i, Qt.UserRole + 1) == current_text:
                        index = i
                        break
            if index >= 0:
                combo.setCurrentIndex(index)
        combo._refresh_closed_text()
        return combo

    def add_device_row(self, category, row_state=None):
        limit = int(self.combo_addr_limit.currentText())
        if self.get_total_qty() >= limit:
            self._warn("add_failed_title", "add_failed_message", limit=limit)
            return

        row_state = self.product_db.resolve_row_state(row_state or self._default_row_snapshot(category))
        self.table.blockSignals(True)
        row = self.table.rowCount()
        self.table.insertRow(row)

        index_item = QTableWidgetItem(str(row + 1))
        index_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        index_item.setTextAlignment(Qt.AlignCenter)
        index_item.setData(Qt.UserRole, row_state)
        self.table.setItem(row, 0, index_item)

        combo = self._create_product_combo(category, row_state.get("product_id"), row_state.get("display_name"))
        self.table.setCellWidget(row, 1, combo)
        self.table.setItem(row, 1, QTableWidgetItem())

        alarm_item = QTableWidgetItem(str(row_state.get("alarm", 0)))
        alarm_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        alarm_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, alarm_item)

        lead_item = QTableWidgetItem(str(row_state.get("lead_dist", "0")))
        lead_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, lead_item)

        interval_item = QTableWidgetItem(str(row_state.get("interval_dist", "10.0")))
        interval_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, interval_item)

        spin = QSpinBox()
        spin.setRange(1, 999)
        spin.setAlignment(Qt.AlignCenter)
        spin.setValue(int(row_state.get("qty", 1)))
        self.table.setCellWidget(row, 5, spin)

        self._connect_product_combo(combo, row)
        spin.valueChanged.connect(lambda value, r=row, s=spin: self._qty_changed(r, s))

        self._sync_combo_selection(row, combo, row_state=row_state)
        self._qty_changed(row, spin)
        self.table.blockSignals(False)
        self.run_calculation()

    def _connect_product_combo(self, combo, row):
        combo.currentIndexChanged.connect(lambda idx, r=row, c=combo: self._sync_combo_selection(r, c))
        combo.activated.connect(lambda idx, r=row, c=combo: self._sync_combo_selection(r, c))

    def _qty_changed(self, row, spin):
        value = spin.value()
        limit = int(self.combo_addr_limit.currentText())
        total = self.get_total_qty()
        if total > limit:
            other_total = total - value
            max_allowed = max(1, limit - other_total)
            self._warn("qty_warning_title", "qty_warning_message", total=total, limit=limit, max_allowed=max_allowed)
            spin.blockSignals(True)
            spin.setValue(max_allowed)
            spin.blockSignals(False)
        interval_item = self.table.item(row, 4)
        if interval_item:
            flags = interval_item.flags() | Qt.ItemIsEnabled | Qt.ItemIsEditable
            if spin.value() <= 1:
                interval_item.setFlags(flags & ~Qt.ItemIsEditable)
            else:
                interval_item.setFlags(flags)
        self._refresh_interval_backgrounds()
        self.run_calculation()

    def _sync_combo_selection(self, row, combo, row_state=None):
        option = combo.currentData(Qt.UserRole + 2)
        merged = {
            "product_id": None,
            "display_name": combo.itemData(combo.currentIndex(), Qt.UserRole + 1) or "",
            "category": row_state.get("category", "") if row_state else "",
            "standby": 0.5,
            "alarm": 0.0,
            "ledCost": 1,
            "type": row_state.get("type", "") if row_state else "",
            "customer_name": "",
            "factory_name": "",
            "product_name": combo.itemData(combo.currentIndex(), Qt.UserRole + 1) or "",
        }
        if isinstance(option, dict):
            merged.update(
                {
                    "product_id": option["product_id"],
                    "display_name": option["display_name"],
                    "category": option["category"],
                    "standby": float(option["standby"]),
                    "alarm": float(option["alarm"]),
                    "ledCost": int(option["ledCost"]),
                    "type": option["type"],
                    "customer_name": option["customer_name"],
                    "factory_name": option["factory_name"],
                    "product_name": option["product_name"],
                }
            )
        if row_state:
            merged.update({k: v for k, v in row_state.items() if v not in (None, "")})
        merged["display_name"] = combo.itemData(combo.currentIndex(), Qt.UserRole + 1) or merged.get("display_name", "")
        index_item = self.table.item(row, 0)
        if index_item:
            index_item.setData(Qt.UserRole, merged)
        alarm_item = self.table.item(row, 2)
        if alarm_item:
            alarm_item.setText(str(merged["alarm"]))

    def _refresh_interval_backgrounds(self):
        enabled = QColor(self.main_app.p["surface"])
        disabled = QColor(self.main_app.p["surface_alt"])
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 4)
            spin = self.table.cellWidget(row, 5)
            if item and isinstance(spin, QSpinBox):
                item.setBackground(disabled if spin.value() <= 1 else enabled)

    def delete_selected(self):
        selection = self.table.selectionModel().selectedRows()
        for idx in sorted(selection, key=lambda x: x.row(), reverse=True):
            self.table.removeRow(idx.row())
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText(str(row + 1))
        self._refresh_interval_backgrounds()
        self.run_calculation()

    def on_table_changed(self, item):
        self.run_calculation()

    def get_aux_current(self):
        try:
            return float(self.edit_aux.text() or 0)
        except Exception:
            return 0

    def get_loop_standby_current(self):
        return getattr(self, "_loop_standby_i", 0)

    def get_loop_alarm_current(self):
        return getattr(self, "_loop_alarm_i", 0)

    def update_battery_display(self, h_std, h_alm):
        self.results["std_time"].setText(f"{h_std:.1f}")
        self.results["alm_time"].setText(f"{h_alm:.2f}")

    def export_state(self):
        rows = []
        for row in range(self.table.rowCount()):
            row_item = self.table.item(row, 0)
            combo = self.table.cellWidget(row, 1)
            alarm_item = self.table.item(row, 2)
            lead_item = self.table.item(row, 3)
            interval_item = self.table.item(row, 4)
            qty_widget = self.table.cellWidget(row, 5)
            if not row_item or not isinstance(combo, QComboBox) or not isinstance(qty_widget, QSpinBox):
                continue
            row_data = dict(row_item.data(Qt.UserRole) or {})
            row_data["display_name"] = combo.itemData(combo.currentIndex(), Qt.UserRole + 1) or row_data.get("display_name", "")
            row_data["alarm"] = float(alarm_item.text() if alarm_item else row_data.get("alarm", 0))
            row_data["lead_dist"] = lead_item.text() if lead_item else "0"
            row_data["interval_dist"] = interval_item.text() if interval_item else "0"
            row_data["qty"] = qty_widget.value()
            rows.append(row_data)
        return {
            "panel_type": self.panel_type,
            "addr_limit_index": self.combo_addr_limit.currentIndex(),
            "cable_index": self.combo_cable.currentIndex(),
            "min_voltage": self.edit_min_voltage.text(),
            "aux_current": self.edit_aux.text(),
            "rows": rows,
        }

    def import_state(self, state):
        self.table.blockSignals(True)
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
        self.combo_addr_limit.setCurrentIndex(state.get("addr_limit_index", 0))
        self.combo_cable.setCurrentIndex(state.get("cable_index", 1))
        self.edit_min_voltage.setText(state.get("min_voltage", "17"))
        self.edit_aux.setText(state.get("aux_current", "0"))
        for row_state in state.get("rows", []):
            self.add_device_row(row_state.get("category", "Other"), row_state=row_state)
        self.table.blockSignals(False)
        self.apply_panel_settings()
        self._refresh_interval_backgrounds()
        self.run_calculation()

    def refresh_products(self):
        self._rebuild_category_buttons()
        for row in range(self.table.rowCount()):
            row_item = self.table.item(row, 0)
            if not row_item:
                continue
            row_data = self.product_db.resolve_row_state(row_item.data(Qt.UserRole) or {})
            category = row_data.get("category", "Other")
            combo = self._create_product_combo(category, row_data.get("product_id"), row_data.get("display_name"))
            self._connect_product_combo(combo, row)
            self.table.removeCellWidget(row, 1)
            self.table.setCellWidget(row, 1, combo)
            self._sync_combo_selection(row, combo, row_state=row_data)
        self.refresh_theme()

    def open_database_manager(self):
        if not self.main_app.admin_authenticated:
            password, ok = QInputDialog.getText(self, self.t("admin_password_title"), self.t("admin_password_label"), QLineEdit.Password)
            if not ok:
                return
            if password != ADMIN_PASSWORD:
                QMessageBox.warning(self, self.t("admin_password_title"), self.t("admin_password_error"))
                return
            self.main_app.admin_authenticated = True
        dialog = ProductDatabaseDialog(self.main_app, self.product_db, self)
        dialog.exec()

    def update_diag_panel(self, errors=None):
        self.last_errors = list(errors or [])
        if not self.last_errors:
            self.diag_panel.setText(self.t("diag_ok"))
            self.diag_panel.setStyleSheet(self.main_app.diag_panel_style(ok=True))
        else:
            self.diag_panel.setText(self.t("diag_error_header") + "\n" + "\n".join(self.last_errors))
            self.diag_panel.setStyleSheet(self.main_app.diag_panel_style(ok=False))

    def run_calculation(self):
        if self.table.rowCount() == 0:
            self._loop_standby_i = 0
            self._loop_alarm_i = 0
            for key, value in self.results.items():
                value.setText("---" if key in {"std_time", "alm_time"} else "0")
            self.update_diag_panel([])
            if hasattr(self.window(), "_recalc_global_battery"):
                self.window()._recalc_global_battery()
            return

        try:
            max_current = float(self.edit_max_current.text() or 400)
            min_voltage = float(self.edit_min_voltage.text() or 17)
            cable = self.combo_cable.currentData()
            if not cable:
                return
            c_res = cable["resistance"]
            total_addr = 0
            total_current = 0
            total_distance = 0
            total_drop = 0
            devices = []
            for row in range(self.table.rowCount()):
                row_item = self.table.item(row, 0)
                qty_widget = self.table.cellWidget(row, 5)
                if not row_item or not isinstance(qty_widget, QSpinBox):
                    continue
                row_data = dict(row_item.data(Qt.UserRole) or {})
                alarm = float(self.table.item(row, 2).text() or 0)
                lead_dist = float(self.table.item(row, 3).text() or 0)
                interval_dist = float(self.table.item(row, 4).text() or 0)
                qty = qty_widget.value()
                total_addr += qty
                devices.append({**row_data, "alarm": alarm, "lead_dist": lead_dist, "interval_dist": interval_dist, "qty": qty})

            led_reserved = sum(d["qty"] * d.get("ledCost", 1) for d in devices if d.get("type") == "LSM" or d.get("ledCost", 1) > 1)
            led_remaining = max(0, MAX_ALARM_LEDS - led_reserved)
            led_used = 0
            processed = []
            for d in devices:
                led_cost = d.get("ledCost", 1) or 1
                active = 0
                if d.get("type") == "LSM" or d.get("ledCost", 1) > 1 or d.get("ledCost", 1) == 0:
                    active = d["qty"]
                else:
                    can_use = led_remaining - led_used
                    if can_use > 0:
                        active = min(d["qty"], can_use // led_cost)
                        led_used += active * led_cost
                row_current = (active * d["alarm"]) + ((d["qty"] - active) * d.get("standby", 0.5))
                total_current += row_current
                processed.append({**d, "row_i": row_current})

            flow = total_current
            for d in processed:
                if d["qty"] <= 0:
                    continue
                lead_r = (c_res * (d["lead_dist"] / 1000.0)) * 2.0
                total_drop += (flow / 1000.0) * lead_r
                total_distance += d["lead_dist"]
                interval_r = (c_res * (d["interval_dist"] / 1000.0)) * 2.0
                if d["qty"] > 1:
                    avg_i = d["row_i"] / d["qty"]
                    flow_after_first = flow - avg_i
                    intervals = d["qty"] - 1
                    factor = intervals * flow_after_first - (intervals * (intervals - 1) / 2.0) * avg_i
                    total_drop += (factor / 1000.0) * interval_r
                    total_distance += intervals * d["interval_dist"]
                flow -= d["row_i"]

            end_voltage = 28.0 - total_drop
            addr_limit = int(self.combo_addr_limit.currentText())
            self.results["addr"].setText(str(total_addr))
            self.units["addr"].setText(f"/{addr_limit}")
            self.results["curr"].setText(f"{total_current:.1f}")
            self.results["volt"].setText(f"{end_voltage:.3f}")
            self.results["lens"].setText(f"{total_distance:.1f}")
            self.results["max_len"].setText(f"{(total_distance * ((28.0 - min_voltage) / total_drop)):.1f}" if total_drop > 0 else str(MAX_CABLE_LENGTH))
            rec_val, rec_unit = "N/A", ""
            for cb in CABLE_TYPES:
                test_drop = (cb["resistance"] / c_res) * total_drop
                if (28.0 - test_drop) >= min_voltage:
                    rec_val, rec_unit = cb["size"], "mm²"
                    break
            self.results["rec_cable"].setText(rec_val)
            self.units["rec_cable"].setText(rec_unit)
            self._loop_standby_i = sum(d["qty"] * d.get("standby", 0.5) for d in devices)
            self._loop_alarm_i = total_current
            if hasattr(self.window(), "_recalc_global_battery"):
                self.window()._recalc_global_battery()
            errors = []
            if total_addr > addr_limit:
                errors.append(self.t("diag_address_over", value=total_addr, limit=addr_limit))
            if total_current > max_current:
                errors.append(self.t("diag_current_over", value=total_current))
            if end_voltage < min_voltage:
                errors.append(self.t("diag_voltage_low", value=end_voltage))
            if total_distance > MAX_CABLE_LENGTH:
                errors.append(self.t("diag_length_over", value=total_distance))
            self.update_diag_panel(errors)
            self.data_changed.emit()
        except Exception as exc:
            print(f"Calculation Error: {exc}")


class CIEMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "zh"
        self.theme = "light"
        self.p = palette(self.theme)
        self.product_db = ProductDatabase(os.path.dirname(__file__))
        self.panel_type = "6002"
        self._syncing = False
        self.admin_authenticated = False
        self.panel_workspaces = {"6002": None, "6004": None}
        self.resize(1400, 900)
        self.workspace_page = QWidget()
        self.setCentralWidget(self.workspace_page)
        self._create_workspace_page()
        self._ensure_workspace_state("6002")
        self.apply_theme(self.theme)
        self.retranslate_ui()
        self._load_workspace("6002")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def t(self, key, **kwargs):
        return tr_text(self.lang, key, **kwargs)

    def _create_pref_controls(self, layout):
        row = QHBoxLayout()
        row.setSpacing(8)
        self.theme_label = QLabel()
        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(lambda: self._on_theme_changed(self.theme_combo.currentData()))
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.currentIndexChanged.connect(lambda: self._on_lang_changed(self.lang_combo.currentData()))
        row.addWidget(self.theme_label)
        row.addWidget(self.theme_combo)
        row.addSpacing(10)
        row.addWidget(self.lang_label)
        row.addWidget(self.lang_combo)
        layout.addLayout(row)

    def _create_workspace_page(self):
        layout = QVBoxLayout(self.workspace_page)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(15)
        self.lbl_panel_info = QLabel()
        self.lbl_loop_count = QLabel("")
        self.panel_selector_label = QLabel()
        top_bar.addWidget(self.lbl_panel_info)
        top_bar.addWidget(self.lbl_loop_count)
        top_bar.addSpacing(20)
        top_bar.addWidget(self.panel_selector_label)

        self.panel_button_group = QButtonGroup(self)
        self.panel_button_group.setExclusive(True)
        self.btn_panel_6002 = QPushButton("6002")
        self.btn_panel_6004 = QPushButton("6004")
        for panel, button in [("6002", self.btn_panel_6002), ("6004", self.btn_panel_6004)]:
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, p=panel: self._switch_panel(p))
            self.panel_button_group.addButton(button)
            top_bar.addWidget(button)

        top_bar.addStretch()
        self._create_pref_controls(top_bar)
        layout.addLayout(top_bar)

        self.workspace_line = QFrame()
        self.workspace_line.setFrameShape(QFrame.HLine)
        layout.addWidget(self.workspace_line)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabCloseRequested.connect(self._close_loop)
        layout.addWidget(self.tab_widget)

    def _fill_pref_combos(self):
        self._syncing = True
        try:
            self.theme_label.setText(f"{self.t('theme')}:")
            self.lang_label.setText(f"{self.t('language')}:")
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            for code, labels in THEME_OPTIONS.items():
                self.theme_combo.addItem(labels.get(self.lang, labels["en"]), code)
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
        self.setStyleSheet(app_style(theme))
        self._fill_pref_combos()
        self._apply_local_theme()
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loop.refresh_theme()

    def retranslate_ui(self):
        self.setWindowTitle(self.t("app_title"))
        self._fill_pref_combos()
        self.lbl_panel_info.setText(self.t("workspace_panel_label", panel=self.panel_type))
        self.lbl_loop_count.setText(self.t("workspace_loop_count", count=self.tab_widget.count(), max_loops=PANEL_SPECS[self.panel_type]["max_loops"]))
        self.panel_selector_label.setText(self.t("panel_selector_label"))
        self._resync_tab_names()
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loop.retranslate_ui()
        self._apply_local_theme()

    def _apply_local_theme(self):
        self.lbl_panel_info.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {self.p['text']};")
        self.lbl_loop_count.setStyleSheet(f"font-size: 13px; color: {self.p['muted']};")
        self.panel_selector_label.setStyleSheet(f"font-size: 13px; color: {self.p['muted']};")
        self.workspace_line.setStyleSheet(f"background-color: {self.p['border']};")
        self.tab_widget.setStyleSheet(self.tab_style())
        self._apply_panel_button_styles()
        self._refresh_close_buttons()

    def primary_button_style(self):
        return f"QPushButton {{ font-weight: bold; background-color: {self.p['accent_soft']}; border: 1px solid {self.p['accent']}; color: {self.p['accent']}; padding: 4px 10px; border-radius: 4px; }} QPushButton:hover {{ background-color: {self.p['hover']}; }}"

    def secondary_button_style(self):
        return f"QPushButton {{ background-color: {self.p['surface_alt']}; border: 1px solid {self.p['border']}; color: {self.p['text']}; padding: 4px 10px; border-radius: 4px; }} QPushButton:hover {{ background-color: {self.p['hover']}; }}"

    def primary_outline_button_style(self):
        return f"QPushButton {{ font-weight: bold; color: {self.p['accent']}; border: 1px solid {self.p['accent']}; border-radius: 4px; background: {self.p['surface']}; }} QPushButton:hover {{ background: {self.p['accent_soft']}; }}"

    def danger_outline_button_style(self):
        return f"QPushButton {{ color: {self.p['danger']}; border: 1px solid {self.p['danger']}; border-radius: 4px; background: {self.p['surface']}; padding: 4px 12px; }} QPushButton:hover {{ background: {self.p['danger_soft']}; }}"

    def colored_outline_button_style(self, color):
        hover_bg = self.p["accent_soft"] if color == self.p["accent"] else self.p["danger_soft"]
        return (
            f"QPushButton {{ font-weight: bold; color: {color}; border: 1px solid {color}; "
            f"border-radius: 4px; background: {self.p['surface']}; padding: 4px 12px; min-height: 28px; }}"
            f"QPushButton:hover {{ background: {hover_bg}; }}"
        )

    def inline_input_style(self):
        return f"border: 1px solid {self.p['border']}; border-radius: 2px; background: {self.p['surface']}; color: {self.p['text']}; padding: 0 2px;"

    def diag_panel_style(self, ok=True):
        bg, fg = (self.p["success_soft"], self.p["success"]) if ok else (self.p["danger_soft"], self.p["danger"])
        return f"QLabel {{ background-color: {bg}; color: {fg}; border: 1px solid {fg}; border-radius: 4px; padding: 10px; font-weight: bold; font-size: 12px; }}"

    def tab_style(self):
        return f"""
QTabWidget::pane {{ border: 1px solid {self.p['border']}; background: {self.p['surface']}; border-radius: 4px; margin-top: 5px; }}
QTabBar::tab {{ padding: 6px 36px 6px 15px; min-width: 80px; font-size: 13px; border: 1px solid {self.p['border']}; border-radius: 6px; background: {self.p['surface_alt']}; color: {self.p['text']}; margin-right: 6px; margin-bottom: 2px; }}
QTabBar::tab:hover {{ background: {self.p['hover']}; color: {self.p['accent']}; border-color: {self.p['accent']}; }}
QTabBar::tab:selected {{ background: {self.p['accent']}; color: white; font-weight: bold; border-color: {self.p['accent']}; }}
QTabBar::close-button {{ width: 0px; height: 0px; margin: 0px; padding: 0px; background: none; border: none; }}
"""

    def close_tab_button_style(self):
        return f"QPushButton {{ border: none; background: transparent; color: {self.p['danger']}; font-size: 14px; font-weight: bold; padding: 0px; margin-right: 8px; }} QPushButton:hover {{ background-color: {self.p['danger']}; color: white; border-radius: 9px; }}"

    def panel_toggle_button_style(self, selected=False):
        if selected:
            return f"QPushButton {{ font-weight: bold; color: white; border: 1px solid {self.p['accent']}; border-radius: 6px; background: {self.p['accent']}; padding: 6px 18px; }}"
        return f"QPushButton {{ font-weight: bold; color: {self.p['text']}; border: 1px solid {self.p['border']}; border-radius: 6px; background: {self.p['surface_alt']}; padding: 6px 18px; }} QPushButton:hover {{ border-color: {self.p['accent']}; color: {self.p['accent']}; }}"

    def _apply_panel_button_styles(self):
        for panel, button in [("6002", self.btn_panel_6002), ("6004", self.btn_panel_6004)]:
            button.setChecked(panel == self.panel_type)
            button.setStyleSheet(self.panel_toggle_button_style(panel == self.panel_type))

    def _refresh_close_buttons(self):
        for index in range(self.tab_widget.count()):
            button = self.tab_widget.tabBar().tabButton(index, QTabBar.RightSide)
            if isinstance(button, QPushButton):
                button.setStyleSheet(self.close_tab_button_style())

    def _question(self, title_key, msg_key, **kwargs):
        box = QMessageBox(QMessageBox.Question, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        set_message_box_texts(box, self)
        return box.exec()

    def _info(self, title_key, msg_key, **kwargs):
        box = QMessageBox(QMessageBox.Information, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        box.setStandardButtons(QMessageBox.Ok)
        set_message_box_texts(box, self)
        return box.exec()

    def _default_workspace_state(self, panel_type):
        return {"panel_type": panel_type, "current_index": 0, "loops": [{"panel_type": panel_type, "addr_limit_index": 0, "cable_index": 1, "min_voltage": "17", "aux_current": "0", "rows": []}]}

    def _ensure_workspace_state(self, panel_type):
        if self.panel_workspaces.get(panel_type) is None:
            self.panel_workspaces[panel_type] = self._default_workspace_state(panel_type)

    def _capture_current_workspace(self):
        loops = []
        for index in range(self.tab_widget.count()):
            loop = self.tab_widget.widget(index)
            if isinstance(loop, LoopEditorWidget):
                loops.append(loop.export_state())
        if not loops:
            loops = self._default_workspace_state(self.panel_type)["loops"]
        self.panel_workspaces[self.panel_type] = {"panel_type": self.panel_type, "current_index": max(0, self.tab_widget.currentIndex()), "loops": loops}

    def _clear_tab_widget(self):
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

    def _load_workspace(self, panel_type):
        self._ensure_workspace_state(panel_type)
        self.panel_type = panel_type
        state = self.panel_workspaces[panel_type]
        self._clear_tab_widget()
        for loop_state in state.get("loops", []):
            self._add_loop(copy_prompt=False, loop_state=loop_state)
        if self.tab_widget.count() == 0:
            self._add_loop(copy_prompt=False)
        self.tab_widget.setCurrentIndex(min(state.get("current_index", 0), self.tab_widget.count() - 1))
        self.lbl_panel_info.setText(self.t("workspace_panel_label", panel=self.panel_type))
        self._update_loop_label()
        self._apply_panel_button_styles()
        self._recalc_global_battery()

    def _switch_panel(self, panel_type):
        if panel_type == self.panel_type:
            return
        self._capture_current_workspace()
        self._load_workspace(panel_type)

    def _update_loop_label(self):
        spec = PANEL_SPECS[self.panel_type]
        self.lbl_loop_count.setText(self.t("workspace_loop_count", count=self.tab_widget.count(), max_loops=spec["max_loops"]))

    def _resync_tab_names(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabText(index, self.t("loop_tab_name", index=index + 1))

    def _add_loop(self, copy_prompt=True, loop_state=None):
        spec = PANEL_SPECS[self.panel_type]
        current_count = self.tab_widget.count()
        if current_count >= spec["max_loops"]:
            self._info("loop_limit_title", "loop_limit_message", panel=self.panel_type, max_loops=spec["max_loops"])
            return
        src_loop = self.tab_widget.currentWidget()
        copy_settings = False
        if copy_prompt and current_count > 0 and isinstance(src_loop, LoopEditorWidget):
            copy_settings = self._question("new_loop_title", "new_loop_message") == QMessageBox.Yes
        loop = LoopEditorWidget(self.panel_type, self.product_db, self)
        if loop_state:
            loop.import_state(loop_state)
        elif copy_settings and isinstance(src_loop, LoopEditorWidget):
            state = src_loop.export_state()
            state["rows"] = []
            loop.import_state(state)
        else:
            loop.apply_panel_settings()
        index = self.tab_widget.addTab(loop, "")
        self._resync_tab_names()
        self.tab_widget.setCurrentWidget(loop)
        self._update_loop_label()
        loop.edit_aux.textChanged.connect(self._recalc_global_battery)
        loop.data_changed.connect(self._capture_current_workspace)
        self._inject_red_close_button(index)
        self._capture_current_workspace()

    def _inject_red_close_button(self, index):
        button = QPushButton("✕")
        button.setFixedSize(18, 18)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(self.close_tab_button_style())
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
            self._capture_current_workspace()

    def _clear_current_panel_config(self):
        if self._question("clear_config_title", "clear_config_message", panel=self.panel_type) == QMessageBox.Yes:
            self.panel_workspaces[self.panel_type] = self._default_workspace_state(self.panel_type)
            self._load_workspace(self.panel_type)

    def _recalc_global_battery(self):
        spec = PANEL_SPECS.get(self.panel_type, PANEL_SPECS["6002"])
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("windowsvista")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    window = CIEMainWindow()
    window.show()
    sys.exit(app.exec())
