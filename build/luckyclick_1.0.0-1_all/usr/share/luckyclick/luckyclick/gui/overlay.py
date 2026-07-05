"""
Overlay window for recording click positions.
Appears as a small draggable window at the top-right corner of the screen.
Shows real-time coordinates and instructions.

Handles HiDPI scaling to ensure coordinates match physical pixels.
Supports 3 drag zones for different click types (left, right, double).
"""

import logging

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QFrame, QApplication, QHBoxLayout)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal)
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QCursor

logger = logging.getLogger(__name__)


class DragOverlay(QWidget):
    """Small overlay window for recording click positions by drag & drop.
    
    Has 3 drag zones for different click types:
    - Left button (green)
    - Right button (red)
    - Double click (blue)
    """

    point_recorded = pyqtSignal(int, int, str)  # x, y, click_type
    coord_updated = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._dragging = False
        self._mouse_pressed = False
        self._drag_click_type = 'left'
        self._setup_ui()

    def _get_scale_factor(self) -> float:
        """Get the device pixel ratio (HiDPI scale factor) of the screen.
        
        Returns:
            float: Scale factor (1.0 = standard, 2.0 = Retina/HiDPI, etc.)
        """
        screen = QApplication.primaryScreen()
        if screen:
            return screen.devicePixelRatio()
        return 1.0

    def _physical_coords(self, logical_x: int, logical_y: int) -> tuple:
        """Convert logical Qt coordinates to physical screen coordinates.
        
        On HiDPI displays, logical pixels differ from physical pixels.
        uinput and X11 expect physical pixel coordinates for accurate positioning.
        
        Args:
            logical_x: X coordinate in logical pixels (from Qt)
            logical_y: Y coordinate in logical pixels (from Qt)
            
        Returns:
            Tuple of (physical_x, physical_y) in physical pixels
        """
        scale = self._get_scale_factor()
        return (int(logical_x * scale), int(logical_y * scale))

    def _setup_ui(self):
        """Setup the overlay UI with 3 drag zones."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        
        self.setFixedSize(200, 140)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
        """)
        
        f = QVBoxLayout()
        f.setContentsMargins(4, 2, 4, 2)
        f.setSpacing(2)
        
        # Title
        title = QLabel("🎯 LuckyClick")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #2E7D32;")
        f.addWidget(title)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #A5D6A7; max-height: 1px;")
        f.addWidget(sep)
        
        # Instruction
        self.instruction = QLabel(
            "Kéo thả vào vị trí cần click\n"
            "(Drag & drop to click point)"
        )
        self.instruction.setAlignment(Qt.AlignCenter)
        self.instruction.setWordWrap(True)
        self.instruction.setStyleSheet("font-size: 8px; color: #333;")
        f.addWidget(self.instruction)
        
        # Coordinates
        self.coord = QLabel("X: ---  Y: ---")
        self.coord.setAlignment(Qt.AlignCenter)
        self.coord.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #1565C0; "
            "background: rgba(200, 230, 255, 150); border-radius: 3px; padding: 1px;"
        )
        f.addWidget(self.coord)
        
        # === 3 Drag Zones ===
        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(3)
        
        # Left click zone
        self.left_zone = QFrame()
        self.left_zone.setFixedHeight(28)
        self.left_zone.setStyleSheet("""
            QFrame {
                background-color: rgba(76, 175, 80, 200);
                border-radius: 4px;
            }
        """)
        left_lbl = QLabel("🖱 Trái\n(Left)")
        left_lbl.setAlignment(Qt.AlignCenter)
        left_lbl.setStyleSheet("font-size: 7px; color: white; font-weight: bold;")
        left_zone_layout = QVBoxLayout()
        left_zone_layout.setContentsMargins(2, 1, 2, 1)
        left_zone_layout.addWidget(left_lbl)
        self.left_zone.setLayout(left_zone_layout)
        zones_layout.addWidget(self.left_zone)
        
        # Right click zone
        self.right_zone = QFrame()
        self.right_zone.setFixedHeight(28)
        self.right_zone.setStyleSheet("""
            QFrame {
                background-color: rgba(244, 67, 54, 200);
                border-radius: 4px;
            }
        """)
        right_lbl = QLabel("🖱 Phải\n(Right)")
        right_lbl.setAlignment(Qt.AlignCenter)
        right_lbl.setStyleSheet("font-size: 7px; color: white; font-weight: bold;")
        right_zone_layout = QVBoxLayout()
        right_zone_layout.setContentsMargins(2, 1, 2, 1)
        right_zone_layout.addWidget(right_lbl)
        self.right_zone.setLayout(right_zone_layout)
        zones_layout.addWidget(self.right_zone)
        
        # Double click zone
        self.double_zone = QFrame()
        self.double_zone.setFixedHeight(28)
        self.double_zone.setStyleSheet("""
            QFrame {
                background-color: rgba(33, 150, 243, 200);
                border-radius: 4px;
            }
        """)
        double_lbl = QLabel("🔄 Double\n(Double)")
        double_lbl.setAlignment(Qt.AlignCenter)
        double_lbl.setStyleSheet("font-size: 7px; color: white; font-weight: bold;")
        double_zone_layout = QVBoxLayout()
        double_zone_layout.setContentsMargins(2, 1, 2, 1)
        double_zone_layout.addWidget(double_lbl)
        self.double_zone.setLayout(double_zone_layout)
        zones_layout.addWidget(self.double_zone)
        
        f.addLayout(zones_layout)
        
        # Exit hint
        exit_lbl = QLabel("Bấm F4 để thoát (Press F4 to exit)")
        exit_lbl.setAlignment(Qt.AlignCenter)
        exit_lbl.setStyleSheet("font-size: 7px; color: #999;")
        f.addWidget(exit_lbl)
        
        self.frame.setLayout(f)
        layout.addWidget(self.frame)
        self.setLayout(layout)
        
        QTimer.singleShot(50, self._position_top_right)

    def _position_top_right(self):
        """Position overlay at top-right."""
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self.move(g.right() - self.width() - 10, g.top() + 10)

    def update_coordinates(self, x: int, y: int):
        """Update displayed coordinates (convert to physical pixels for display)."""
        phys_x, phys_y = self._physical_coords(x, y)
        self.coord.setText(f"X: {phys_x}  Y: {phys_y}")

    def _get_global_pos(self) -> tuple:
        """Get current mouse position safely using QCursor.
        
        Returns:
            Tuple of (logical_x, logical_y) in logical pixels from Qt
        """
        pos = QCursor.pos()
        return pos.x(), pos.y()

    def _get_click_type_from_pos(self, pos_y: int) -> str:
        """Determine which click type zone the mouse is over based on Y position.
        
        The overlay has 3 zones at the bottom. We check if the mouse is
        over the overlay and which zone it's in.
        
        Args:
            pos_y: Y position relative to overlay
            
        Returns:
            'left', 'right', or 'double'
        """
        # Zones are at the bottom of the overlay (approx y 80-130)
        # Left: 0-33%, Right: 33-66%, Double: 66-100% of zones area
        if not hasattr(self, 'left_zone'):
            return 'left'
        
        # Get zone positions relative to overlay
        left_geo = self.left_zone.geometry()
        right_geo = self.right_zone.geometry()
        double_geo = self.double_zone.geometry()
        
        # Check which zone the mouse is over (using global coordinates)
        global_pos = QCursor.pos()
        overlay_pos = self.mapToGlobal(self.rect().topLeft())
        
        # Map to overlay-relative coordinates
        rel_x = global_pos.x() - overlay_pos.x()
        rel_y = global_pos.y() - overlay_pos.y()
        
        if left_geo.contains(rel_x, rel_y):
            return 'left'
        elif right_geo.contains(rel_x, rel_y):
            return 'right'
        elif double_geo.contains(rel_x, rel_y):
            return 'double'
        
        return 'left'  # Default

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._dragging = True
            
            # Determine click type from the zone that was pressed
            self._drag_click_type = self._get_click_type_from_pos(event.pos().y())
            
            # Show which zone is active
            zone_names = {
                'left': '🖱 Trái (Left)',
                'right': '🖱 Phải (Right)',
                'double': '🔄 Double'
            }
            self.instruction.setText(
                f"🔄 Đang kéo {zone_names[self._drag_click_type]}...\n"
                "Thả chuột để ghi điểm"
            )
            
            # Start a timer to track mouse during drag
            self._drag_timer = QTimer()
            self._drag_timer.timeout.connect(self._track_mouse)
            self._drag_timer.start(50)

    def _track_mouse(self):
        """Track mouse position during drag (QCursor, no event needed)."""
        if not self._dragging:
            return
        logical_x, logical_y = self._get_global_pos()
        # Emit physical coordinates for accurate click positioning
        phys_x, phys_y = self._physical_coords(logical_x, logical_y)
        self.update_coordinates(logical_x, logical_y)
        self.coord_updated.emit(phys_x, phys_y)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging and event.button() == Qt.LeftButton:
            self._dragging = False
            self._mouse_pressed = False
            
            if hasattr(self, '_drag_timer'):
                self._drag_timer.stop()
            
            logical_x, logical_y = self._get_global_pos()
            # Convert to physical coordinates before emitting
            phys_x, phys_y = self._physical_coords(logical_x, logical_y)
            # Emit with click type
            self.point_recorded.emit(phys_x, phys_y, self._drag_click_type)
            
            zone_names = {
                'left': '🖱 Trái',
                'right': '🖱 Phải',
                'double': '🔄 Double'
            }
            self.instruction.setText(
                f"✅ Đã ghi {zone_names[self._drag_click_type]}!\n"
                "Kéo thả tiếp hoặc bấm F4"
            )
            QTimer.singleShot(1500, self._reset_instruction)

    def _reset_instruction(self):
        self.instruction.setText(
            "Kéo thả vào vị trí cần click\n"
            "(Drag & drop to click point)"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self._position_top_right()
        self.raise_()