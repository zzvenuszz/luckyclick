"""
Main window for LuckyClick auto clicker.
Light theme, bilingual (Vietnamese/English), system tray support.
"""

import os
import json
import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QLineEdit, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QRadioButton,
    QCheckBox, QSlider, QSystemTrayIcon, QMenu, QAction,
    QMessageBox, QFileDialog, QApplication, QFrame, QGridLayout,
    QSizePolicy, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette

from luckyclick.core.clicker import AutoClicker
from luckyclick.core.recorder import PointRecorder
from luckyclick.core.hotkey_manager import HotkeyManager
from luckyclick.gui.overlay import DragOverlay
# Click effect overlay removed due to stability issues

logger = logging.getLogger(__name__)

# Bilingual strings
STR = {
    'app_title': 'LuckyClick - Auto Clicker',
    'interval': 'Khoảng cách (Interval):',
    'hours': 'giờ (h)',
    'minutes': 'phút (m)',
    'seconds': 'giây (s)',
    'milliseconds': 'ms',
    'click_type': 'Loại click (Click type):',
    'left': 'Chuột trái (Left)',
    'right': 'Chuột phải (Right)',
    'middle': 'Chuột giữa (Middle)',
    'double': 'Double click',
    'hotkey': 'Phím tắt (Hotkey):',
    'start_stop': 'Bắt đầu/Dừng (Start/Stop)',
    'record': 'Chế độ record (Record mode)',
    'click_count': 'Số lần click (Click count):',
    'unlimited': 'Vô hạn (Unlimited)',
    'limited': 'Có giới hạn (Limited):',
    'times': 'lần (times)',
    'auto_hide': 'Tự động ẩn khi chạy (Auto-hide on start)',
    'random_delay': 'Random delay (%):',
    'points_list': 'Danh sách điểm click (Click points):',
    'no_points': 'Chưa có điểm nào. Bấm F4 để record.',
    'action_column': 'Thao tác (Action)',
    'delay_column': 'Delay (ms)',
    'smart_delay': 'Áp dụng Smart Delay',
    'add_key': 'Thêm phím',
    'key_capture_prompt': 'Nhấn phím hoặc tổ hợp phím cần thêm...',
    'start_btn': '▶ Bắt đầu (Start)',
    'stop_btn': '⏹ Dừng (Stop)',
    'delete_btn': 'Xóa (Delete)',
    'clear_all_btn': 'Xóa tất cả (Clear all)',
    'save_btn': 'Lưu profile (Save)',
    'load_btn': 'Tải profile (Load)',
    'click_count_label': 'Đã click: {count} lần',
    'recording_on': '🎯 ĐANG RECORD...',
    'recording_off': 'Chế độ record (F4)',
    'started': '▶ Auto click đang chạy...',
    'stopped': '⏹ Auto click đã dừng',
    'finished': '✅ Hoàn thành {count} lần click!',
    'tray_show': 'Hiện (Show)',
    'tray_hide': 'Ẩn (Hide)',
    'tray_quit': 'Thoát (Quit)',
    'confirm_delete': 'Xóa điểm này? (Delete this point?)',
    'confirm_clear': 'Xóa tất cả điểm? (Clear all points?)',
    'error_no_points': 'Chưa có điểm click nào! (No click points!)',
    'error': 'Lỗi (Error)',
    'info': 'Thông báo (Info)',
    'profile_saved': 'Đã lưu profile! (Profile saved!)',
    'profile_loaded': 'Đã tải profile! (Profile loaded!)',
    'about': 'Giới thiệu (About)',
    'about_text': 'LuckyClick v1.0.0\nAuto Clicker cho Linux\n🍀 Cỏ may mắn mang đến thành công!',
    'custom_hotkey_prompt': 'Bấm phím bạn muốn làm phím tắt...\n(Press the key you want as hotkey...)',
    'single_instance': 'LuckyClick đã chạy rồi!\n(LuckyClick is already running!)',
    'smart_click': 'Chế độ Smart Click',
    'click_at_cursor': 'Click tại vị trí chuột (Click at cursor)',
}


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal to safely trigger hotkey actions from background threads
    # This prevents Qt crashes when hotkey callbacks fire from pynput threads
    hotkey_triggered = pyqtSignal(str)
    key_action_captured = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        # Core components
        self.clicker = AutoClicker()
        self.recorder = PointRecorder()
        self.hotkey_manager = HotkeyManager()
        self.overlay = DragOverlay()
        
        # State
        self._recording_mode = False
        self._auto_hide = True
        self._running = False
        self._current_hotkey = 'F8'  # Default start/stop hotkey
        self._smart_click = False
        self._recording_restore_window = False
        
        # Setup UI
        self._setup_ui()
        self._setup_tray()
        self._setup_hotkeys()
        self._setup_callbacks()
        
        # Connect hotkey signal to main thread handler
        self.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.key_action_captured.connect(self._on_key_action_captured)
        
        # Start hotkey listener
        self.hotkey_manager.start()
        
        # Click count timer
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_click_count)
        self._update_timer.start(500)

    def _setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle(STR['app_title'])
        self.setMinimumSize(500, 600)
        self.setMaximumSize(600, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # === Title ===
        title_label = QLabel("🍀 LuckyClick")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px; font-weight: bold; color: #2E7D32;
            padding: 4px;
        """)
        main_layout.addWidget(title_label)
        
        subtitle = QLabel("Auto Clicker for Linux")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px; color: #666; margin-bottom: 8px;")
        main_layout.addWidget(subtitle)
        
        # === Settings Group ===
        settings_group = QGroupBox("Cài đặt (Settings)")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 1px solid #BDBDBD;
                border-radius: 6px; margin-top: 8px; padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px; padding: 0 5px;
            }
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(6)
        
        # Interval row - compact layout with labels
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(4)
        interval_layout.addWidget(QLabel(STR['interval']))
        
        # Hours
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 99)
        self.hours_spin.setValue(0)
        self.hours_spin.setFixedWidth(55)
        self.hours_spin.setSuffix("h")
        interval_layout.addWidget(self.hours_spin)
        h_lbl = QLabel(STR['hours'].split('(')[1].rstrip(')'))
        h_lbl.setStyleSheet("font-size: 10px; color: #666;")
        interval_layout.addWidget(h_lbl)
        
        # Minutes
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(0)
        self.minutes_spin.setFixedWidth(55)
        self.minutes_spin.setSuffix("m")
        interval_layout.addWidget(self.minutes_spin)
        m_lbl = QLabel(STR['minutes'].split('(')[1].rstrip(')'))
        m_lbl.setStyleSheet("font-size: 10px; color: #666;")
        interval_layout.addWidget(m_lbl)
        
        # Seconds
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setValue(5)
        self.seconds_spin.setFixedWidth(55)
        self.seconds_spin.setSuffix("s")
        interval_layout.addWidget(self.seconds_spin)
        s_lbl = QLabel(STR['seconds'].split('(')[1].rstrip(')'))
        s_lbl.setStyleSheet("font-size: 10px; color: #666;")
        interval_layout.addWidget(s_lbl)
        
        # Milliseconds
        self.ms_spin = QSpinBox()
        self.ms_spin.setRange(0, 999)
        self.ms_spin.setValue(0)
        self.ms_spin.setFixedWidth(65)
        self.ms_spin.setSuffix("ms")
        interval_layout.addWidget(self.ms_spin)
        ms_lbl = QLabel("ms")
        ms_lbl.setStyleSheet("font-size: 10px; color: #666;")
        interval_layout.addWidget(ms_lbl)
        
        interval_layout.addStretch()
        settings_layout.addLayout(interval_layout)
        
        # Click type + Hotkey row
        row_layout = QHBoxLayout()
        
        # Click type
        row_layout.addWidget(QLabel(STR['click_type']))
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems([
            STR['left'], STR['right'], STR['middle'], STR['double']
        ])
        self.click_type_combo.setFixedWidth(126)
        row_layout.addWidget(self.click_type_combo)
        
        row_layout.addSpacing(20)
        
        # Hotkey
        row_layout.addWidget(QLabel(STR['hotkey']))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(HotkeyManager.get_available_keys())
        self.hotkey_combo.setCurrentText('F8')
        self.hotkey_combo.setFixedWidth(45)
        row_layout.addWidget(self.hotkey_combo)
        
        row_layout.addStretch()
        settings_layout.addLayout(row_layout)
        
        # Click count row
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel(STR['click_count']))
        
        self.unlimited_radio = QRadioButton(STR['unlimited'])
        self.unlimited_radio.setChecked(True)
        count_layout.addWidget(self.unlimited_radio)
        
        self.limited_radio = QRadioButton(STR['limited'])
        count_layout.addWidget(self.limited_radio)
        
        self.max_clicks_spin = QSpinBox()
        self.max_clicks_spin.setRange(1, 999999)
        self.max_clicks_spin.setValue(100)
        self.max_clicks_spin.setEnabled(False)
        self.max_clicks_spin.setFixedWidth(100)
        count_layout.addWidget(self.max_clicks_spin)
        
        count_layout.addWidget(QLabel(STR['times']))
        count_layout.addStretch()
        settings_layout.addLayout(count_layout)
        
        # Connect radio buttons
        self.unlimited_radio.toggled.connect(
            lambda checked: self.max_clicks_spin.setEnabled(not checked)
        )
        
        # Auto-hide checkbox
        self.auto_hide_check = QCheckBox(STR['auto_hide'])
        self.auto_hide_check.setChecked(True)
        settings_layout.addWidget(self.auto_hide_check)
        
        # Random delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel(STR['random_delay']))
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setRange(0, 100)
        self.delay_slider.setValue(0)
        self.delay_slider.setFixedWidth(200)
        delay_layout.addWidget(self.delay_slider)
        self.delay_label = QLabel("0%")
        self.delay_label.setFixedWidth(40)
        delay_layout.addWidget(self.delay_label)
        self.delay_slider.valueChanged.connect(
            lambda v: self.delay_label.setText(f"{v}%")
        )
        delay_layout.addStretch()
        settings_layout.addLayout(delay_layout)
        
        # === Smart Click Mode ===
        smart_layout = QHBoxLayout()
        self.smart_click_check = QCheckBox(STR['smart_click'])
        self.smart_click_check.setChecked(False)
        self.smart_click_check.toggled.connect(self._on_smart_click_toggled)
        smart_layout.addWidget(self.smart_click_check)
        self.smart_delay_check = QCheckBox(STR['smart_delay'])
        self.smart_delay_check.setChecked(False)
        smart_layout.addWidget(self.smart_delay_check)
        smart_layout.addStretch()
        settings_layout.addLayout(smart_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # === Points List Group ===
        points_group = QGroupBox(STR['points_list'])
        points_group.setStyleSheet(settings_group.styleSheet())
        points_layout = QVBoxLayout()
        
        self.points_list = QListWidget()
        self.points_list.setAlternatingRowColors(True)
        self.points_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.points_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.points_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: #FAFAFA;
                alternate-background-color: #F0F0F0;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:selected {
                background-color: #C8E6C9;
                color: #1B5E20;
            }
        """)
        self.points_list.setMinimumHeight(0)
        list_header = QHBoxLayout()
        list_header.setContentsMargins(8, 0, 8, 0)
        list_header.addWidget(QLabel(STR['action_column']), 1)
        delay_header = QLabel(STR['delay_column'])
        delay_header.setFixedWidth(115)
        list_header.addWidget(delay_header)
        points_layout.addLayout(list_header)
        points_layout.addWidget(self.points_list)
        
        # Points control buttons
        points_btn_layout = QHBoxLayout()
        
        self.record_btn = QPushButton(STR['recording_off'])
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white;
                border: none; padding: 6px 12px; border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        points_btn_layout.addWidget(self.record_btn)

        self.add_key_btn = QPushButton(STR['add_key'])
        self.add_key_btn.clicked.connect(self._start_key_action_capture)
        points_btn_layout.addWidget(self.add_key_btn)
        
        self.delete_btn = QPushButton(STR['delete_btn'])
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336; color: white;
                border: none; padding: 6px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        points_btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton(STR['clear_all_btn'])
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575; color: white;
                border: none; padding: 6px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        points_btn_layout.addWidget(self.clear_btn)
        
        points_btn_layout.addStretch()
        points_layout.addLayout(points_btn_layout)
        
        points_group.setLayout(points_layout)
        points_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(points_group, 1)
        
        # === Control Buttons ===
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(STR['start_btn'])
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                border: none; padding: 10px 24px; border-radius: 6px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #A5D6A7; }
        """)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(STR['stop_btn'])
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336; color: white;
                border: none; padding: 10px 24px; border-radius: 6px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:disabled { background-color: #EF9A9A; }
        """)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        
        # Profile buttons
        self.save_btn = QPushButton(STR['save_btn'])
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        control_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton(STR['load_btn'])
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        control_layout.addWidget(self.load_btn)
        
        main_layout.addLayout(control_layout)
        
        # === Status Bar ===
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Sẵn sàng (Ready)")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        self.click_count_label = QLabel(STR['click_count_label'].format(count=0))
        self.click_count_label.setStyleSheet("color: #1565C0; font-size: 11px; font-weight: bold;")
        status_layout.addWidget(self.click_count_label)
        
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
        
        central.setLayout(main_layout)
        
        # Apply light theme
        self._apply_light_theme()
        
        # Connect buttons
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.record_btn.clicked.connect(self._toggle_recording)
        self.delete_btn.clicked.connect(self._delete_point)
        self.clear_btn.clicked.connect(self._clear_points)
        self.save_btn.clicked.connect(self._save_profile)
        self.load_btn.clicked.connect(self._load_profile)
        
        # Connect hotkey combo change
        self.hotkey_combo.currentTextChanged.connect(self._on_hotkey_combo_changed)

    def _apply_light_theme(self):
        """Apply light theme stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QWidget {
                font-family: 'Noto Sans', 'DejaVu Sans', sans-serif;
                font-size: 12px;
                color: #333;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 6px 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QComboBox {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FAFAFA;
            }
            QComboBox:hover {
                border-color: #4CAF50;
            }
            QSpinBox, QLineEdit {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 4px;
                background-color: #FAFAFA;
            }
            QSpinBox:hover, QLineEdit:hover {
                border-color: #4CAF50;
            }
            QCheckBox {
                spacing: 6px;
            }
            QRadioButton {
                spacing: 6px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #388E3C;
            }
        """)

    def _setup_tray(self):
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a simple pixmap for tray icon (will be replaced by actual icon)
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction(STR['tray_show'], self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction(STR['tray_hide'], self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction(STR['tray_quit'], self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        self.tray_icon.show()

    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        # F4 for recording mode (hardcoded, critical function)
        self.hotkey_manager.register_hotkey('F4', self._on_f4_hotkey)
        
        # F8 for start/stop (default, can be changed)
        self._current_hotkey = 'F8'
        self.hotkey_manager.register_hotkey(self._current_hotkey, self._on_start_stop_hotkey)

    def _on_f4_hotkey(self):
        """Handle F4 hotkey press (from background thread).
        
        Uses signal to dispatch to main thread to prevent Qt crashes.
        """
        self.hotkey_triggered.emit('f4')

    def _on_start_stop_hotkey(self):
        """Handle start/stop hotkey press (from background thread).
        
        Uses signal to dispatch to main thread to prevent Qt crashes.
        """
        self.hotkey_triggered.emit('start_stop')

    def _on_hotkey_triggered(self, action: str):
        """Handle hotkey actions on the main thread (connected via pyqtSignal).
        
        This runs on the Qt main thread, so all UI operations are safe.
        
        Args:
            action: 'f4' to toggle recording, 'start_stop' to toggle auto-click
        """
        if action == 'f4':
            self._toggle_recording()
        elif action == 'start_stop':
            self._toggle_start_stop()

    def _on_hotkey_combo_changed(self, text: str):
        """Handle hotkey combo box selection change.
        
        If 'Custom' is selected, enter key capture mode.
        Otherwise, dynamically re-register the start/stop hotkey.
        """
        if text == 'Tùy chỉnh (Custom)':
            self._start_custom_hotkey_capture()
            return
        
        # Re-register hotkey with the new key
        if text and text != self._current_hotkey:
            # Unregister old hotkey
            self.hotkey_manager.unregister_hotkey(self._current_hotkey)
            # Register new hotkey
            self._current_hotkey = text
            self.hotkey_manager.register_hotkey(text, self._on_start_stop_hotkey)
            logger.info(f"Start/Stop hotkey changed to: {text}")

    def _on_smart_click_toggled(self, checked: bool):
        """Handle Smart Click checkbox toggle.
        
        When Smart Click is enabled:
        - Plays recorded click and keyboard actions in order
        - Click type dropdown is disabled (recorded click types override)
        - Smart Delay checkbox selects per-action delays instead of the global interval
        
        When Smart Click is disabled:
        - Uses the global click type from dropdown
        - Click type dropdown is enabled
        """
        self._smart_click = checked
        self.click_type_combo.setEnabled(not checked)
        if checked:
            self.status_label.setText("🧠 Chế độ Smart Click - Click theo danh sách đã record")
        else:
            self.status_label.setText("Sẵn sàng (Ready)")
        logger.info(f"Smart Click {'enabled' if checked else 'disabled'}")

    def _start_custom_hotkey_capture(self):
        """Start capturing a custom hotkey from the user."""
        self.status_label.setText(STR['custom_hotkey_prompt'])
        self.status_label.setStyleSheet("color: #FF9800; font-size: 11px; font-weight: bold;")
        
        # Start capture in hotkey manager
        self.hotkey_manager.start_capture(self._on_custom_key_captured)

    def _on_custom_key_captured(self, key_str: str):
        """Called when a custom key is captured.
        
        Note: This runs on a background thread from pynput.
        We use invokeMethod or a signal to update UI on main thread.
        """
        # Use QTimer to invoke on main thread
        QTimer.singleShot(0, lambda: self._apply_custom_hotkey(key_str))

    def _apply_custom_hotkey(self, key_str: str):
        """Apply the captured custom hotkey (runs on main thread)."""
        # Unregister old hotkey
        self.hotkey_manager.unregister_hotkey(self._current_hotkey)
        
        # Register new custom hotkey
        self._current_hotkey = key_str
        self.hotkey_manager.register_hotkey(key_str, self._on_start_stop_hotkey)
        
        # Update combo box (temporarily block signals to avoid recursion)
        self.hotkey_combo.blockSignals(True)
        # Add the custom key to combo if not present
        idx = self.hotkey_combo.findText(key_str)
        if idx < 0:
            # Insert before the "Custom" option
            custom_idx = self.hotkey_combo.findText('Tùy chỉnh (Custom)')
            if custom_idx >= 0:
                self.hotkey_combo.insertItem(custom_idx, key_str)
                idx = custom_idx
            else:
                self.hotkey_combo.addItem(key_str)
                idx = self.hotkey_combo.count() - 1
        self.hotkey_combo.setCurrentIndex(idx)
        self.hotkey_combo.blockSignals(False)
        
        # Update status
        self.status_label.setText(f"✅ Phím tắt (Hotkey): {key_str}")
        self.status_label.setStyleSheet("color: #2E7D32; font-size: 11px; font-weight: bold;")
        
        logger.info(f"Custom hotkey captured and registered: {key_str}")

    def _setup_callbacks(self):
        """Setup callbacks for core components."""
        # Clicker callbacks
        self.clicker.on_click = self._on_click
        self.clicker.on_stop = self._on_clicker_stop
        self.clicker.on_finished = self._on_clicker_finished
        
        # Recorder callbacks
        self.recorder.on_point_recorded = self._on_point_recorded
        
        # Overlay callbacks
        self.overlay.point_recorded.connect(self._on_overlay_point)
        self.overlay.coord_updated.connect(self._on_coord_updated)

    def _toggle_recording(self):
        """Toggle recording mode on/off."""
        if self._running:
            logger.warning("Recording mode cannot be entered while auto click is running")
            self.status_label.setText("Không thể record khi auto click đang chạy")
            return
        if self._recording_mode:
            self._exit_recording_mode()
        else:
            self._enter_recording_mode()

    def _enter_recording_mode(self):
        """Enter recording mode, hiding the main window behind the overlay."""
        if self._running:
            logger.warning("Recording mode cannot be entered while auto click is running")
            return
        self._recording_restore_window = self.isVisible()
        self._recording_mode = True
        self.overlay.show()
        self.hide()
        self.record_btn.setText(STR['recording_on'])
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336; color: white;
                border: none; padding: 6px 12px; border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        self.status_label.setText("🎯 Chế độ record - Kéo thả chuột từ overlay")
        logger.info("Recording mode entered")

    def _exit_recording_mode(self):
        """Exit recording mode - hide overlay."""
        self._recording_mode = False
        self.overlay.hide()
        self.record_btn.setText(STR['recording_off'])
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white;
                border: none; padding: 6px 12px; border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.status_label.setText("Sẵn sàng (Ready)")
        if self._recording_restore_window:
            self.show()
            self.raise_()
            self.activateWindow()
        self._recording_restore_window = False
        logger.info("Recording mode exited")

    def _on_overlay_point(self, x: int, y: int, click_type: str = 'left'):
        """Handle a point recorded from the overlay."""
        self.recorder.add_point(x, y, click_type)

    def _on_coord_updated(self, x: int, y: int):
        """Handle coordinate update from overlay."""
        self.status_label.setText(f"📍 Tọa độ (Coordinates): X={x}, Y={y}")

    def _on_point_recorded(self, point: dict):
        """Handle a new click or key action recorded."""
        if not self.smart_click_check.isChecked():
            self.smart_click_check.setChecked(True)
        if point['type'] == 'key':
            logger.info(
                "Recorded key action #%d: keys=%s",
                len(self.recorder.get_points()), '+'.join(point['keys'])
            )
        else:
            logger.info(
                "Recorded point #%d: position=%d:%d px type=%s smart_checkbox=%s mode=%s",
                len(self.recorder.get_points()), point['x'], point['y'],
                point['click_type'], self.smart_click_check.isChecked(),
                'smart' if self._smart_click else 'normal'
            )
        self._refresh_points_list()

    def _start_key_action_capture(self):
        """Capture a single key or key combination for the action sequence."""
        self.status_label.setText(STR['key_capture_prompt'])
        self.status_label.setStyleSheet(
            "color: #FF9800; font-size: 11px; font-weight: bold;"
        )
        self.hotkey_manager.start_capture(
            lambda keys: self.key_action_captured.emit(keys),
            combination=True
        )

    def _on_key_action_captured(self, keys: str):
        """Add the captured key action on the Qt main thread."""
        self.recorder.add_key_action(keys.split('+'))
        self.status_label.setText("✅ Đã thêm phím: {}".format(keys))
        self.status_label.setStyleSheet(
            "color: #2E7D32; font-size: 11px; font-weight: bold;"
        )

    def _set_action_delay(self, index: int, delay_ms: int):
        """Persist an edited delay from a row's spin box."""
        self.recorder.set_delay(index, delay_ms)

    def _refresh_points_list(self):
        """Refresh the points list widget."""
        self.points_list.clear()
        points = self.recorder.get_points()
        
        if not points:
            item = QListWidgetItem(STR['no_points'])
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(QColor('#999'))
            self.points_list.addItem(item)
            return
        
        for i, point in enumerate(points):
            if point['type'] == 'key':
                description = "⌨  {}".format('+'.join(point['keys']))
            else:
                type_symbol = {
                    'left': '🖱', 'right': '🖱R',
                    'double': '🔄', 'middle': '🖱M'
                }.get(point['click_type'], '')
                description = "X: {}  Y: {}  {}".format(
                    point['x'], point['y'], type_symbol
                )

            row = QWidget()
            row.setFixedHeight(30)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 0, 8, 0)
            row_layout.addWidget(QLabel("#{}  {}".format(i + 1, description)), 1)
            delay_spin = QSpinBox()
            delay_spin.setRange(0, 3600000)
            delay_spin.setSingleStep(1000)
            delay_spin.setSuffix(" ms")
            delay_spin.setFixedWidth(115)
            delay_spin.setFixedHeight(30)
            delay_spin.setValue(point.get('delay_ms', 1000))
            delay_spin.valueChanged.connect(
                lambda value, index=i: self._set_action_delay(index, value)
            )
            row_layout.addWidget(delay_spin)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.points_list.addItem(item)
            self.points_list.setItemWidget(item, row)

    def _delete_point(self):
        """Delete the selected point."""
        current = self.points_list.currentRow()
        if current >= 0:
            reply = QMessageBox.question(
                self, STR['confirm_delete'],
                STR['confirm_delete'],
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.recorder.remove_point(current)
                self._refresh_points_list()

    def _clear_points(self):
        """Clear all points."""
        if self.recorder.get_points():
            reply = QMessageBox.question(
                self, STR['confirm_clear'],
                STR['confirm_clear'],
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.recorder.clear_points()
                self._refresh_points_list()

    def _toggle_start_stop(self):
        """Toggle auto clicker start/stop."""
        if self._running:
            self._on_stop()
        else:
            self._on_start()

    def _on_start(self):
        """Start auto clicking.
        
        If Smart Click is enabled:
        - Uses the recorded click and keyboard action sequence
        - Smart Delay optionally applies each action's recorded delay
        - Requires at least one recorded point
        
        If Smart Click is disabled:
        - Uses a single point at current cursor position
        - Uses the global click type from dropdown
        - Does NOT require any recorded points
        """
        if self._recording_mode:
            self._exit_recording_mode()

        # Get points (needed for both modes)
        points = self.recorder.get_points()
        logger.info(
            "Start requested: smart_checkbox=%s internal_mode=%s recorded_points=%d",
            self.smart_click_check.isChecked(),
            'smart' if self._smart_click else 'normal', len(points)
        )
        
        # Smart Click mode requires at least one recorded point
        if self._smart_click:
            if not points:
                QMessageBox.warning(self, STR['error'], STR['error_no_points'])
                return
        
        # Get interval in milliseconds
        interval = (
            self.hours_spin.value() * 3600000 +
            self.minutes_spin.value() * 60000 +
            self.seconds_spin.value() * 1000 +
            self.ms_spin.value()
        )
        if interval < 10:
            interval = 10  # Minimum 10ms
        
        # Get click type
        click_type_map = {
            STR['left']: 'left',
            STR['right']: 'right',
            STR['middle']: 'middle',
            STR['double']: 'double'
        }
        click_type = click_type_map.get(self.click_type_combo.currentText(), 'left')
        
        # Get max clicks
        max_clicks = 0 if self.unlimited_radio.isChecked() else self.max_clicks_spin.value()
        
        # Configure clicker
        if self._smart_click:
            # Smart Click: use the recorded click and keyboard action sequence.
            self.clicker.points = points
            self.clicker.smart_click = True
        else:
            # Normal mode: use cursor position with global click type
            # No need for recorded points - just click at current cursor position
            # Convert to physical coordinates for consistency with recorded points
            from PyQt5.QtGui import QCursor
            cursor_pos = QCursor.pos()
            # Apply same HiDPI scaling as overlay for coordinate consistency
            screen = QApplication.primaryScreen()
            scale = screen.devicePixelRatio() if screen else 1.0
            phys_x = int(cursor_pos.x() * scale)
            phys_y = int(cursor_pos.y() * scale)
            self.clicker.points = [(phys_x, phys_y, click_type)]
            self.clicker.smart_click = False
        
        self.clicker.interval_ms = interval
        self.clicker.click_type = click_type
        self.clicker.max_clicks = max_clicks
        self.clicker.random_delay_pct = self.delay_slider.value()
        self.clicker.smart_delay = (
            self._smart_click and self.smart_delay_check.isChecked()
        )
        
        # Start
        self.clicker.start()
        self._running = True
        self.record_btn.setEnabled(False)
        self.add_key_btn.setEnabled(False)
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(STR['started'])
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        
        # Auto-hide to tray
        if self.auto_hide_check.isChecked():
            self.hide()
            self.tray_icon.showMessage(
                "LuckyClick",
                "▶ Auto click đang chạy...\nBấm F8 để dừng",
                QSystemTrayIcon.Information,
                2000
            )
        
        logger.info(
            "Auto click started: mode=%s recorded_points=%d active_points=%d "
            "interval_ms=%d global_type=%s",
            'smart' if self.clicker.smart_click else 'normal', len(points),
            len(self.clicker.points), interval, click_type
        )

    def _on_stop(self):
        """Stop auto clicking."""
        self.clicker.stop()
        self._running = False
        
        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.record_btn.setEnabled(True)
        self.add_key_btn.setEnabled(True)
        self.status_label.setText(STR['stopped'])
        self.status_label.setStyleSheet("color: #F44336; font-size: 11px;")
        
        # Show window if hidden
        if self.auto_hide_check.isChecked() and not self.isVisible():
            self.show()
            self.tray_icon.showMessage(
                "LuckyClick",
                "⏹ Auto click đã dừng",
                QSystemTrayIcon.Information,
                2000
            )
        
        logger.info("Auto click stopped by user")

    def _on_click(self, x: int, y: int, count: int):
        """Called on each click with position and count.
        
        Args:
            x: X coordinate of the click
            y: Y coordinate of the click
            count: Current click count
        """
        self.click_count_label.setText(STR['click_count_label'].format(count=count))

    def _on_clicker_stop(self):
        """Called when clicker stops."""
        self._running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.record_btn.setEnabled(True)
        self.add_key_btn.setEnabled(True)

    def _on_clicker_finished(self):
        """Called when clicker finishes all clicks."""
        self._running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.record_btn.setEnabled(True)
        self.add_key_btn.setEnabled(True)
        self.status_label.setText(STR['finished'].format(count=self.clicker.click_count))
        self.status_label.setStyleSheet("color: #2E7D32; font-size: 11px; font-weight: bold;")
        
        # Show window
        if not self.isVisible():
            self.show()
            self.tray_icon.showMessage(
                "LuckyClick",
                STR['finished'].format(count=self.clicker.click_count),
                QSystemTrayIcon.Information,
                3000
            )

    def _update_click_count(self):
        """Update click count display."""
        if self._running:
            self.click_count_label.setText(
                STR['click_count_label'].format(count=self.clicker.click_count)
            )

    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def _save_profile(self):
        """Save current configuration to a JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, STR['save_btn'], 'luckyclick_profile.json',
            'JSON Files (*.json)'
        )
        if filepath:
            profile = {
                'points': self.recorder.get_points(),
                'interval': {
                    'hours': self.hours_spin.value(),
                    'minutes': self.minutes_spin.value(),
                    'seconds': self.seconds_spin.value(),
                    'milliseconds': self.ms_spin.value()
                },
                'click_type': self.click_type_combo.currentText(),
                'hotkey': self._current_hotkey,
                'unlimited': self.unlimited_radio.isChecked(),
                'max_clicks': self.max_clicks_spin.value(),
                'auto_hide': self.auto_hide_check.isChecked(),
                'random_delay': self.delay_slider.value(),
                'smart_delay': self.smart_delay_check.isChecked(),
            }
            try:
                with open(filepath, 'w') as f:
                    json.dump(profile, f, indent=2)
                QMessageBox.information(self, STR['info'], STR['profile_saved'])
            except Exception as e:
                QMessageBox.critical(self, STR['error'], str(e))

    def _load_profile(self):
        """Load configuration from a JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, STR['load_btn'], '',
            'JSON Files (*.json)'
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    profile = json.load(f)
                
                # Load points
                if 'points' in profile:
                    points = profile['points']
                    self.recorder.set_points(points)
                    self.smart_click_check.setChecked(bool(points))
                    self._refresh_points_list()
                    logger.info(
                        "Profile points loaded: count=%d smart_mode=%s",
                        len(points), self._smart_click
                    )
                
                # Load interval
                if 'interval' in profile:
                    inv = profile['interval']
                    self.hours_spin.setValue(inv.get('hours', 0))
                    self.minutes_spin.setValue(inv.get('minutes', 0))
                    self.seconds_spin.setValue(inv.get('seconds', 5))
                    self.ms_spin.setValue(inv.get('milliseconds', 0))
                
                # Load click type
                if 'click_type' in profile:
                    idx = self.click_type_combo.findText(profile['click_type'])
                    if idx >= 0:
                        self.click_type_combo.setCurrentIndex(idx)
                
                # Load hotkey
                if 'hotkey' in profile:
                    hotkey = profile['hotkey']
                    # Remove old hotkey
                    self.hotkey_manager.unregister_hotkey(self._current_hotkey)
                    self._current_hotkey = hotkey
                    self.hotkey_manager.register_hotkey(hotkey, self._on_start_stop_hotkey)
                    
                    # Update combo box
                    self.hotkey_combo.blockSignals(True)
                    idx = self.hotkey_combo.findText(hotkey)
                    if idx < 0:
                        custom_idx = self.hotkey_combo.findText('Tùy chỉnh (Custom)')
                        if custom_idx >= 0:
                            self.hotkey_combo.insertItem(custom_idx, hotkey)
                            idx = custom_idx
                        else:
                            self.hotkey_combo.addItem(hotkey)
                            idx = self.hotkey_combo.count() - 1
                    self.hotkey_combo.setCurrentIndex(idx)
                    self.hotkey_combo.blockSignals(False)
                
                # Load click count mode
                if 'unlimited' in profile:
                    self.unlimited_radio.setChecked(profile['unlimited'])
                    self.limited_radio.setChecked(not profile['unlimited'])
                
                if 'max_clicks' in profile:
                    self.max_clicks_spin.setValue(profile['max_clicks'])
                
                if 'auto_hide' in profile:
                    self.auto_hide_check.setChecked(profile['auto_hide'])
                
                if 'random_delay' in profile:
                    self.delay_slider.setValue(profile['random_delay'])

                self.smart_delay_check.setChecked(profile.get('smart_delay', False))
                
                QMessageBox.information(self, STR['info'], STR['profile_loaded'])
                
            except Exception as e:
                QMessageBox.critical(self, STR['error'], str(e))

    def _quit_app(self):
        """Quit the application."""
        self.clicker.cleanup()
        self.hotkey_manager.stop()
        self.overlay.close()
        QApplication.quit()

    def closeEvent(self, event):
        """Handle close event - minimize to tray instead of quitting."""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self._quit_app()
            event.accept()

    def set_app_icon(self, icon: QIcon):
        """Set the application icon."""
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)