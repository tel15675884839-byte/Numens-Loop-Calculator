import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QPushButton, QGroupBox, QHeaderView, QFrame, QAbstractItemView,
                             QMessageBox, QStyledItemDelegate, QSpinBox, QDoubleSpinBox, QGridLayout, 
                             QDialog, QDialogButtonBox, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QDoubleValidator, QIntValidator

# --- Constants ---
ADDRESS_LIMIT = 125
MAX_ALARM_LEDS = 10
MAX_CABLE_LENGTH = 1000

CABLE_TYPES = [
    {'size': '1.0', 'resistance': 18.1, 'label': '1.0 mm²'},
    {'size': '1.5', 'resistance': 12.1, 'label': '1.5 mm²'},
    {'size': '2.5', 'resistance': 7.41, 'label': '2.5 mm²'},
    {'size': '4.0', 'resistance': 4.61, 'label': '4.0 mm²'},
]

NATIVE_COMPACT_STYLE = """
QMainWindow { background-color: #f5f6f7; }
QGroupBox { font-weight: bold; border: 1px solid #dcdfe6; border-radius: 6px; margin-top: 12px; padding: 10px; background-color: white; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -6px; color: #409eff; }
QLineEdit, QComboBox, QSpinBox { height: 26px; border: 1px solid #dcdfe6; border-radius: 4px; padding: 0 5px; }
QLineEdit:focus, QComboBox:focus { border-color: #409eff; }

/* 卡片勋章风格 (方案 3) */
#resCard, #suggestCard { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 6px 10px; margin-bottom: 4px; }
#resCard:hover { background-color: #ffffff; border-color: #dcdfe6; }
#resName { color: #495057; font-size: 13px; font-weight: 500; }
#resVal { font-weight: bold; font-family: 'Segoe UI', system-ui; font-size: 16px; color: #343a40; }
#resUnit { color: #6c757d; font-size: 11px; font-weight: bold; padding-left: 2px; }

#suggestCard { background-color: #f0f7ff; border: 1px solid #c2e0ff; }
#suggestName { color: #004085; font-size: 13px; font-weight: bold; }
#suggestVal { font-weight: bold; font-family: 'Segoe UI'; font-size: 16px; color: #007bff; }
"""

class NumericDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        dv = QDoubleValidator(0.0, 9999.0, 2, editor)
        dv.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(dv)
        return editor

class BatchAddDialog(QDialog):
    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.devices = devices
        self.setWindowTitle("添加设备")
        self.resize(850, 550)
        self.results = [] # List of (preset, qty)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 10, 10, 10); main_layout.setSpacing(10)
        
        # Scroll area for many devices
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        # Group by optimized category
        # Map original types to readable categories
        category_map = {
            "Detector": "1. 探测器 (Detectors)",
            "MCP": "2. 手动报警按钮 (MCPs)",
            "Sounder": "3. 声光报警器 (Sounders)",
            "Input Module": "4. 模块 & IO (Modules / IO)",
            "Output Module": "4. 模块 & IO (Modules / IO)",
            "Input/Output Module": "4. 模块 & IO (Modules / IO)",
            "Zone Input Module": "4. 模块 & IO (Modules / IO)",
            "LSM Module": "4. 模块 & IO (Modules / IO)"
        }
        
        # Prepare categorized data
        categorized = {}
        for d in self.devices:
            original_type = d.get('type', 'Other')
            cat = category_map.get(original_type, "5. 其他 (Others)")
            if cat not in categorized: categorized[cat] = []
            categorized[cat].append(d)
            
        self.spin_boxes = [] # Store (preset, QSpinBox)
        
        # Sort category names to ensure consistent order
        for cat in sorted(categorized.keys()):
            gp = QGroupBox(cat)
            gp_layout = QGridLayout(gp)
            gp_layout.setVerticalSpacing(5)
            gp_layout.setHorizontalSpacing(10)
            
            models = categorized[cat]
            if "模块 & IO" in cat:
                # Group 1: 620, 621, 622 etc.
                others = sorted([m for m in models if "626-" not in m['name']], key=lambda x: x['name'])
                # Group 2: 626 series sorted to stack vertically (ON above OFF) in 4 columns
                s626_on = sorted([m for m in models if "626-" in m['name'] and "LEDs on" in m['name']], key=lambda x: x['name'])
                s626_off = sorted([m for m in models if "626-" in m['name'] and "LEDs disabled" in m['name']], key=lambda x: x['name'])
                models = others + s626_on + s626_off
            else:
                models.sort(key=lambda x: x['name'])
            
            num_cols = 4
            for i, d in enumerate(models):
                row = i // num_cols
                col_base = (i % num_cols) * 2
                
                # Simplify name for display if it has long parenthetical
                display_name = d['name']
                if "LEDs disabled" in display_name:
                    display_name = display_name.replace("LEDs disabled", "LED关")
                elif "LEDs on" in display_name:
                    display_name = display_name.replace("LEDs on", "LED开")
                
                lbl = QLabel(display_name)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl.setToolTip(d['name']) # Keep full name in tooltip
                
                sb = QSpinBox()
                sb.setRange(0, 250)
                sb.setFixedWidth(50)
                sb.setAlignment(Qt.AlignCenter)
                
                gp_layout.addWidget(lbl, row, col_base)
                gp_layout.addWidget(sb, row, col_base + 1)
                
                gp_layout.setColumnStretch(col_base, 0)
                gp_layout.setColumnStretch(col_base + 1, 1)
                
                self.spin_boxes.append((d, sb))
            
            scroll_layout.addWidget(gp)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("确认添加")
        btn_ok.setMinimumHeight(35)
        btn_ok.setStyleSheet("font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("取消")
        btn_cancel.setMinimumHeight(35)
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        main_layout.addLayout(btn_box)

    def get_selection(self):
        final = []
        for preset, sb in self.spin_boxes:
            if sb.value() > 0:
                final.append((preset, sb.value()))
        return final

class LoopCalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devices = self.load_device_data()
        self.setWindowTitle("Numens 回路计算器")
        self.resize(1000, 750)
        self.setStyleSheet(NATIVE_COMPACT_STYLE)
        self.init_ui()
        self.setup_connections()
        self.on_panel_changed()
        
    def load_device_data(self):
        json_path = os.path.join(os.path.dirname(__file__), "devices_new.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
        return [{"name": "Generic Device", "standby": 0.5, "alarm": 2.0, "ledCost": 1, "type": "Detector"}]

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setContentsMargins(15, 10, 15, 15); main_layout.setSpacing(10)
        
        # Global Style
        self.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 1.2em;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding-left: 5px;
                padding-right: 5px;
                left: 10px;
            }
            QLabel { font-size: 13px; }
            QPushButton { font-size: 13px; }
            QLineEdit, QComboBox { font-size: 13px; }
        """)
        
        # 1. System Parameters
        sys_group = QGroupBox("1. 系统参数"); sys_layout = QHBoxLayout(sys_group)
        sys_layout.setContentsMargins(10, 15, 10, 10); sys_layout.setSpacing(15)
        
        for lbl, key in [("主机:", "panel"), ("回路设备数:", "addr_limit"), ("回路电流(mA):", "cur"), ("最低电压(V):", "volt"), ("电缆规格:", "cable")]:
            hbox = QHBoxLayout(); hbox.addWidget(QLabel(lbl))
            if key == "panel":
                self.combo_panel = QComboBox(); self.combo_panel.addItems(["6004", "6002"]); hbox.addWidget(self.combo_panel)
            elif key == "addr_limit":
                self.combo_addr_limit = QComboBox(); self.combo_addr_limit.addItems(["125", "250"]); hbox.addWidget(self.combo_addr_limit)
            elif key == "cur":
                self.edit_max_current = QLineEdit("400"); self.edit_max_current.setFixedWidth(60); self.edit_max_current.setEnabled(False); hbox.addWidget(self.edit_max_current)
            elif key == "volt":
                self.edit_min_voltage = QLineEdit("17"); self.edit_min_voltage.setFixedWidth(60); self.edit_min_voltage.setValidator(QDoubleValidator(0.0, 30.0, 1)); hbox.addWidget(self.edit_min_voltage)
            else:
                self.combo_cable = QComboBox(); self.combo_cable.setMinimumWidth(180)
                for ct in CABLE_TYPES: self.combo_cable.addItem(f"{ct['label']} ({ct['resistance']}Ω/km)", ct)
                self.combo_cable.setCurrentIndex(1); hbox.addWidget(self.combo_cable)
            sys_layout.addLayout(hbox)
        sys_layout.addStretch(); main_layout.addWidget(sys_group)
        
        # Work Area
        work_area = QHBoxLayout(); work_area.setSpacing(15)
        
        # 2. Device List
        dev_group = QGroupBox("2. 设备清单"); dev_layout = QVBoxLayout(dev_group); dev_layout.setContentsMargins(10, 15, 10, 10)
        toolbar = QHBoxLayout(); 
        self.btn_batch = QPushButton("添加设备..."); self.btn_add_custom = QPushButton("添加自定义设备"); self.btn_delete = QPushButton("删除选中")
        self.btn_batch.setStyleSheet("font-weight: bold; background-color: #f8f8f8; border: 1px solid #007aff; color: #007aff; padding: 3px 10px;")
        
        toolbar.addWidget(self.btn_batch); toolbar.addWidget(self.btn_add_custom); toolbar.addWidget(self.btn_delete); toolbar.addStretch()
        dev_layout.addLayout(toolbar)
        
        self.table = QTableWidget(0, 6)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels(["序号", "设备名称", "报警(mA)", "距前节点(m)", "组内间距(m)", "数量"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 45); self.table.setColumnWidth(2, 80); self.table.setColumnWidth(3, 90); self.table.setColumnWidth(4, 90); self.table.setColumnWidth(5, 70)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegateForColumn(2, NumericDelegate()); self.table.setItemDelegateForColumn(3, NumericDelegate()); self.table.setItemDelegateForColumn(4, NumericDelegate())
        self.table.verticalHeader().setVisible(False)
        dev_layout.addWidget(self.table)
        
        work_area.addWidget(dev_group, 7)
        
        # 3. Calculation Results
        # 3. Calculation Results
        res_group = QGroupBox("3. 计算结果"); res_layout = QVBoxLayout(res_group); res_layout.setContentsMargins(8, 15, 8, 10); res_layout.setSpacing(4)
        
        self.results = {}; self.units = {}
        
        # --- Section: Real-time Status ---
        status_label = QLabel("当前回路状态:"); status_label.setStyleSheet("color: #909399; font-weight: bold; font-size: 11px;")
        res_layout.addWidget(status_label)
        
        for key, name, unit in [('addr', '点数负载', f'/{ADDRESS_LIMIT}'), ('curr', '回路总电流', 'mA'), ('volt', '末端最低电压', 'V'), ('lens', '回路累计线长', 'm')]:
            card = QFrame(); card.setObjectName("resCard"); card_layout = QHBoxLayout(card); card_layout.setContentsMargins(8, 4, 8, 4)
            
            name_lbl = QLabel(name); name_lbl.setObjectName("resName")
            val_lbl = QLabel("0.0"); val_lbl.setObjectName("resVal"); val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            unt_lbl = QLabel(unit); unt_lbl.setObjectName("resUnit"); unt_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            card_layout.addWidget(name_lbl)
            card_layout.addStretch()
            card_layout.addWidget(val_lbl)
            card_layout.addWidget(unt_lbl)
            
            res_layout.addWidget(card)
            self.results[key] = val_lbl; self.units[key] = unt_lbl

        res_layout.addSpacing(5)
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken); line.setStyleSheet("background-color: #dcdfe6;"); res_layout.addWidget(line); res_layout.addSpacing(5)

        # --- Section: Safety Optimization ---
        opt_label = QLabel("安全优化建议:"); opt_label.setStyleSheet("color: #409eff; font-weight: bold; font-size: 11px;")
        res_layout.addWidget(opt_label)

        for key, name, unit in [('max_len', '极限施工距离', 'm'), ('rec_cable', '推荐最小线径', '')]:
            card = QFrame(); card.setObjectName("suggestCard"); card_layout = QHBoxLayout(card); card_layout.setContentsMargins(8, 4, 8, 4)
            
            name_lbl = QLabel(name); name_lbl.setObjectName("suggestName")
            val_lbl = QLabel("N/A"); val_lbl.setObjectName("suggestVal"); val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            unt_lbl = QLabel(unit); unt_lbl.setObjectName("resUnit"); unt_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            card_layout.addWidget(name_lbl)
            card_layout.addStretch()
            card_layout.addWidget(val_lbl)
            card_layout.addWidget(unt_lbl)
            
            res_layout.addWidget(card)
            self.results[key] = val_lbl; self.units[key] = unt_lbl
        
        res_layout.addStretch(); work_area.addWidget(res_group, 3)
        main_layout.addLayout(work_area)

    def setup_connections(self):
        self.btn_batch.clicked.connect(self.show_batch_dialog); self.btn_add_custom.clicked.connect(self.add_custom_device); self.btn_delete.clicked.connect(self.delete_selected)
        self.table.itemChanged.connect(self.on_table_changed)
        self.combo_panel.currentIndexChanged.connect(self.on_panel_changed); self.combo_cable.currentIndexChanged.connect(self.run_calculation)
        self.edit_min_voltage.textChanged.connect(self.run_calculation)
        self.combo_addr_limit.currentIndexChanged.connect(self.validate_all_quantities)
        self.combo_addr_limit.currentIndexChanged.connect(self.run_calculation)

    def on_panel_changed(self):
        is_6004 = self.combo_panel.currentText() == "6004"
        self.edit_max_current.setText("400") # 两台主机默认电流都是 400mA
        # 6004不支持250，锁定为125；6002支持切换
        if is_6004:
            self.combo_addr_limit.setCurrentIndex(0) # 强制125
            self.combo_addr_limit.setEnabled(False)
        else:
            self.combo_addr_limit.setEnabled(True)
        # 切换限额后检查是否有数据超标
        self.validate_all_quantities()
        self.run_calculation()

    def validate_all_quantities(self):
        limit = int(self.combo_addr_limit.currentText())
        total = 0
        for r in range(self.table.rowCount()):
            sb = self.table.cellWidget(r, 5)
            if sb: total += sb.value()
        
        if total > limit:
            QMessageBox.warning(self, "设备总数超限", 
                f"当前总设备数({total})超过了回路限制({limit})！\n建议调整设备数量。")
            # 可以在此处增加自动扣减逻辑，但根据需求先提示

    def get_total_qty(self):
        total = 0
        for r in range(self.table.rowCount()):
            sb = self.table.cellWidget(r, 5)
            if sb: total += sb.value()
        return total

    def show_batch_dialog(self):
        dlg = BatchAddDialog(self.devices, self)
        if dlg.exec():
            selections = dlg.get_selection()
            
            # 批量操作预检
            added_qty = sum(qty for _, qty in selections)
            current_qty = self.get_total_qty()
            limit = int(self.combo_addr_limit.currentText())
            
            if current_qty + added_qty > limit:
                QMessageBox.warning(self, "批量添加提醒", 
                    f"所选设备总数({added_qty})与现有设备({current_qty})之和将超过回路限制({limit})！\n请减少添加数量。")
                return

            for preset, qty in selections:
                self.add_device(custom_data=preset, qty=qty)

    def add_device(self, custom_data=None, qty=1):
        if not custom_data: return
        is_p = (not custom_data.get('custom', False))
        
        self.table.blockSignals(True)
        r = self.table.rowCount(); self.table.insertRow(r)
        
        it0 = QTableWidgetItem(str(r+1)); it0.setFlags(Qt.ItemIsEnabled); it0.setTextAlignment(Qt.AlignCenter); self.table.setItem(r, 0, it0)
        it1 = QTableWidgetItem(custom_data['name']); it1.setData(Qt.UserRole, custom_data)
        if is_p: it1.setFlags(it1.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, 1, it1)
        it2 = QTableWidgetItem(str(custom_data['alarm'])); it2.setTextAlignment(Qt.AlignCenter)
        if is_p: it2.setFlags(it2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, 2, it2)
        it3 = QTableWidgetItem("10.0" if r > 0 else "0.0"); it3.setTextAlignment(Qt.AlignCenter); self.table.setItem(r, 3, it3)
        it4 = QTableWidgetItem("10.0"); it4.setTextAlignment(Qt.AlignCenter); self.table.setItem(r, 4, it4)
        
        sb = QSpinBox(); sb.setRange(1, 999); sb.setValue(qty); sb.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(r, 5, sb)
        
        def on_qty_changed(val):
            # 获取当前行 (防止行删除后索引错位)
            curr_row = -1
            for row in range(self.table.rowCount()):
                if self.table.cellWidget(row, 5) == sb:
                    curr_row = row
                    break
            if curr_row == -1: return

            # 验证回路总数上限
            limit = int(self.combo_addr_limit.currentText())
            total = 0
            for row in range(self.table.rowCount()):
                w = self.table.cellWidget(row, 5)
                if w: total += w.value()
            
            if total > limit:
                # 计算除了当前变动外的总数
                other_total = total - val
                max_allowed = max(0, limit - other_total)
                
                QMessageBox.warning(self, "超限提示", 
                    f"总设备数({total})超过了回路限制({limit})！\n该项最大允许设置为: {max_allowed}")
                
                sb.blockSignals(True)
                sb.setValue(max_allowed if max_allowed > 0 else 1)
                sb.blockSignals(False)
                val = sb.value()

            # 更新组内间距编辑状态
            item = self.table.item(curr_row, 4)
            if item:
                if val <= 1:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    item.setBackground(QColor("#f0f0f0"))
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    item.setBackground(QColor("#ffffff"))
            self.run_calculation()
            
        sb.valueChanged.connect(on_qty_changed)
        # 初始触发一次以设定状态
        on_qty_changed(qty)
        
        self.table.blockSignals(False); self.run_calculation()
        
    def add_custom_device(self):
        limit = int(self.combo_addr_limit.currentText())
        if self.get_total_qty() >= limit:
            QMessageBox.warning(self, "添加失败", f"当前回路点数已达上限({limit})，无法继续添加！")
            return
        self.add_device(custom_data={"name": "自定义设备", "standby": 0.5, "alarm": 10.0, "ledCost": 1, "type": "Detector", "custom": True})

    def delete_selected(self):
        for i in sorted(self.table.selectionModel().selectedRows(), reverse=True): self.table.removeRow(i.row())
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()): self.table.item(i, 0).setText(str(i+1))
        self.table.blockSignals(False); self.run_calculation()

    def on_table_changed(self, item): self.run_calculation()

    def run_calculation(self):
        if self.table.rowCount() == 0:
            for v in self.results.values(): v.setText("0")
            return
        try:
            max_c = float(self.edit_max_current.text() or 400)
            min_v = float(self.edit_min_voltage.text() or 17)
            
            cable_data = self.combo_cable.currentData()
            if not cable_data: return
            c_res = cable_data['resistance']
            
            total_addr, total_i, dist, drop = 0, 0, 0, 0
            device_data = []
            
            for i in range(self.table.rowCount()):
                item_name = self.table.item(i, 1)
                if not item_name: continue
                orig = item_name.data(Qt.UserRole) or {"standby":0.5, "ledCost":1, "type":"Detector"}
                
                item_alarm = self.table.item(i, 2)
                alarm = float(item_alarm.text() or 0) if item_alarm else 0
                
                item_lead = self.table.item(i, 3)
                lead_dist = float(item_lead.text() or 0) if item_lead else 0
                
                item_interval = self.table.item(i, 4)
                interval_dist = float(item_interval.text() or 0) if item_interval else 0
                
                qty_widget = self.table.cellWidget(i, 5)
                qty = qty_widget.value() if qty_widget else 1
                
                device_data.append({**orig, 'alarm': alarm, 'lead_dist': lead_dist, 'interval_dist': interval_dist, 'qty': qty})
                total_addr += qty
            
            if not device_data:
                for v in self.results.values(): v.setText("0")
                return

            # LED Power Management
            slots_p = sum(d['qty']*d.get('ledCost', 1) for d in device_data if d['type'] == 'LSM' or d.get('ledCost', 1) > 1)
            rem, used = max(0, MAX_ALARM_LEDS - slots_p), 0
            
            processed = []
            for d in device_data:
                active = 0
                if d['type'] == 'LSM' or d.get('ledCost',1) > 1 or d.get('ledCost',1) == 0: 
                    active = d['qty']
                else: 
                    can = rem - used
                    if can > 0: 
                        active = min(d['qty'], can // (d.get('ledCost', 1) or 1))
                        used += active * d.get('ledCost', 1)
                
                row_i = (active * d['alarm']) + ((d['qty'] - active) * d.get('standby', 0.5))
                total_i += row_i
                processed.append({**d, 'row_i': row_i})

            flow = total_i
            for d in processed:
                if d['qty'] <= 0: continue
                # Resistance of lead distance (applies to the first device in this row)
                # Drop for lead segment: full current `flow` flows through `lead_dist`
                r_lead = (c_res * (d['lead_dist'] / 1000.0)) * 2.0
                drop += (flow / 1000.0) * r_lead
                dist += d['lead_dist']
                
                # Resistance for interval spacing (applies to subsequent devices)
                r_interval = (c_res * (d['interval_dist'] / 1000.0)) * 2.0
                
                # Approximation: we have (qty - 1) intervals.
                # Current drops by (d['row_i']/d['qty']) at each device.
                if d['qty'] > 1:
                    avg_i_per_device = d['row_i'] / d['qty']
                    # Current after the first device
                    flow_after_first = flow - avg_i_per_device
                    
                    intervals = d['qty'] - 1
                    # Total current-intervals for the arithmetic progression
                    # sum(flow_after_first - k * avg_i_per_device) for k=0 to intervals-1
                    fact = intervals * flow_after_first - (intervals * (intervals - 1) / 2.0) * avg_i_per_device
                    drop += (fact / 1000.0) * r_interval
                    dist += intervals * d['interval_dist']
                
                flow -= d['row_i']
            
            v_end = 28.0 - drop
            addr_limit = int(self.combo_addr_limit.currentText())
            
            self.results['addr'].setText(str(total_addr))
            self.results['addr'].setStyleSheet("color: green" if total_addr <= addr_limit else "color: red")
            self.units['addr'].setText(f"/{addr_limit}") # 直接更新单位标签
            
            self.results['curr'].setText(f"{total_i:.1f}")
            self.results['curr'].setStyleSheet("color: green" if total_i <= max_c else "color: red")
            self.results['volt'].setText(f"{v_end:.3f}")
            self.results['volt'].setStyleSheet("color: green" if v_end >= min_v else "color: red")
            self.results['lens'].setText(f"{dist:.1f}")
            self.results['lens'].setStyleSheet("color: green" if dist <= MAX_CABLE_LENGTH else "color: red")

            # --- 双向优化建议逻辑 ---
            # 1. 自动计算极限长度 (基于当前电压门限)
            if drop > 0:
                # 允许的最大压降
                allowed_drop = 28.0 - min_v
                # 极限长度因子 (允许压降 / 当前压降)
                k_limit = allowed_drop / drop
                limit_dist = dist * k_limit
                self.results['max_len'].setText(f"{limit_dist:.1f}")
            else:
                self.results['max_len'].setText(str(MAX_CABLE_LENGTH))

            # 2. 自动推荐线径
            rec_val, rec_unit = "N/A", ""
            for cb in CABLE_TYPES:
                # 根据电阻比例推算该线径下的压降
                test_drop = (cb['resistance'] / c_res) * drop
                if (28.0 - test_drop) >= min_v:
                    rec_val = cb['size']
                    rec_unit = "mm²"
                    break
            self.results['rec_cable'].setText(rec_val)
            self.units['rec_cable'].setText(rec_unit)
        except Exception as e:
            print(f"Calculation Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("windowsvista")
    app.setFont(QFont("Microsoft YaHei", 9))
    window = LoopCalculatorApp(); window.show(); sys.exit(app.exec())
