"""
Click effect overlay for LuckyClick.
Shows visual feedback animations at click positions.
Runs as a transparent overlay window that does not intercept mouse events.

Auto-detects window manager (X11/Wayland) to use appropriate overlay flags.
"""

import math
import logging

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient

from luckyclick.core.wm_detector import detect_window_manager, get_overlay_window_flags

logger = logging.getLogger(__name__)

# Effect types
EFFECT_NONE = 'Không (None)'
EFFECT_RIPPLE = 'Sóng (Ripple)'
EFFECT_FLASH = 'Chớp sáng (Flash)'
EFFECT_CIRCLE = 'Vòng tròn (Circle)'
EFFECT_CROSSHAIR = 'Chữ thập (Crosshair)'

EFFECT_LIST = [EFFECT_NONE, EFFECT_RIPPLE, EFFECT_FLASH, EFFECT_CIRCLE, EFFECT_CROSSHAIR]

# Animation durations (ms)
ANIM_DURATION = 600
ANIM_FPS = 60
ANIM_INTERVAL = 1000 // ANIM_FPS
ANIM_FRAMES = ANIM_DURATION // ANIM_INTERVAL


class ClickEffect:
    """Data class for a single click effect animation instance."""
    
    def __init__(self, x: int, y: int, effect_type: str):
        self.x = x
        self.y = y
        self.effect_type = effect_type
        self.frame = 0
        self.max_frames = ANIM_FRAMES
        self.active = True
    
    @property
    def progress(self) -> float:
        """Animation progress from 0.0 to 1.0."""
        if self.max_frames <= 0:
            return 1.0
        return min(1.0, self.frame / self.max_frames)
    
    @property
    def alpha(self) -> int:
        """Alpha value that fades out over time."""
        return max(0, int(255 * (1.0 - self.progress)))
    
    @property
    def radius(self) -> int:
        """Current radius that expands over time."""
        return int(5 + self.progress * 40)  # 5px to 45px
    
    def tick(self):
        """Advance one frame. Returns True if still active."""
        self.frame += 1
        if self.frame >= self.max_frames:
            self.active = False
        return self.active


class ClickEffectOverlay(QWidget):
    """Full-screen transparent overlay for rendering click animations.
    
    Uses WA_TransparentForMouseEvents so clicks pass through to underlying windows.
    Auto-detects window manager to use appropriate flags.
    Paints visual effects (ripple, flash, circle, crosshair) at recorded positions.
    Effects are drawn in order and cleared one by one as they finish.
    """
    
    def __init__(self):
        super().__init__()
        self._effects: list[ClickEffect] = []
        self._enabled = True
        self._effect_type = EFFECT_RIPPLE
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the overlay window properties based on detected WM."""
        # Detect window manager and get appropriate flags
        wm = detect_window_manager()
        config = get_overlay_window_flags(wm)
        
        self.setWindowFlags(config['flags'])
        for attr, value in config['attributes']:
            self.setAttribute(attr, value)
        
        self.setStyleSheet("background: transparent;")
        
        # Full screen
        self._update_geometry()
        
        # Animation timer
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.setInterval(ANIM_INTERVAL)
    
    def _update_geometry(self):
        """Update to full screen geometry."""
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.geometry()
            self.setGeometry(g)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable click effects.
        
        Args:
            enabled: True to show effects, False to hide
        """
        self._enabled = enabled
        if not enabled:
            self._cleanup()
    
    def set_effect_type(self, effect_type: str):
        """Set the current effect type.
        
        Args:
            effect_type: One of EFFECT_NONE, EFFECT_RIPPLE, EFFECT_FLASH, etc.
        """
        self._effect_type = effect_type
    
    def _cleanup(self):
        """Clean up all effects and hide immediately."""
        self._effects.clear()
        self._anim_timer.stop()
        self.hide()
        self.update()
    
    def show_effect_at(self, x: int, y: int):
        """Trigger a click effect at the given position.
        
        Args:
            x: X coordinate (screen space)
            y: Y coordinate (screen space)
        """
        if not self._enabled or self._effect_type == EFFECT_NONE:
            return
        
        effect = ClickEffect(x, y, self._effect_type)
        self._effects.append(effect)
        
        # Show overlay and start animation
        if not self.isVisible():
            self._update_geometry()
            self.show()
            self.lower()  # Keep behind other windows but still visible
        
        if not self._anim_timer.isActive():
            self._anim_timer.start()
        
        self.update()
    
    def _tick_animation(self):
        """Advance all effects by one frame.
        
        Effects are cleared in order (FIFO) - oldest finishes first.
        """
        # Tick all effects and remove finished ones
        self._effects = [e for e in self._effects if e.tick()]
        
        # Trigger repaint
        self.update()
        
        # Stop timer and hide if no effects remain
        if not self._effects:
            self._anim_timer.stop()
            self.hide()
    
    def paintEvent(self, event):
        """Paint all active effects in order (oldest first)."""
        if not self._effects:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for effect in self._effects:
            self._draw_effect(painter, effect)
        
        painter.end()
    
    def _draw_effect(self, painter: QPainter, effect: ClickEffect):
        """Draw a single effect based on its type.
        
        Args:
            painter: QPainter instance
            effect: ClickEffect to draw
        """
        if effect.effect_type == EFFECT_RIPPLE:
            self._draw_ripple(painter, effect)
        elif effect.effect_type == EFFECT_FLASH:
            self._draw_flash(painter, effect)
        elif effect.effect_type == EFFECT_CIRCLE:
            self._draw_circle(painter, effect)
        elif effect.effect_type == EFFECT_CROSSHAIR:
            self._draw_crosshair(painter, effect)
    
    def _draw_ripple(self, painter: QPainter, effect: ClickEffect):
        """Draw a ripple (expanding ring) effect.
        
        Multiple concentric rings that expand outward with fading opacity.
        """
        alpha = effect.alpha
        radius = effect.radius
        
        # Draw 3 concentric rings at different phases
        for i in range(3):
            r = radius + i * 15
            a = max(0, alpha - i * 60)
            if a <= 0:
                continue
            
            pen = QPen(QColor(76, 175, 80, a))  # Green #4CAF50
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(effect.x, effect.y), r, r)
    
    def _draw_flash(self, painter: QPainter, effect: ClickEffect):
        """Draw a flash (pulsing glow) effect.
        
        A circular glow that expands and fades out.
        """
        alpha = effect.alpha
        radius = effect.radius
        
        # Outer glow
        gradient = QRadialGradient(effect.x, effect.y, radius)
        gradient.setColorAt(0.0, QColor(76, 175, 80, alpha))
        gradient.setColorAt(0.5, QColor(76, 175, 80, alpha // 2))
        gradient.setColorAt(1.0, QColor(76, 175, 80, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPoint(effect.x, effect.y), radius, radius)
        
        # Center bright spot
        center_alpha = min(255, alpha + 50)
        painter.setBrush(QBrush(QColor(255, 255, 255, center_alpha)))
        painter.drawEllipse(QPoint(effect.x, effect.y), 3, 3)
    
    def _draw_circle(self, painter: QPainter, effect: ClickEffect):
        """Draw a simple expanding circle effect."""
        alpha = effect.alpha
        radius = effect.radius
        
        # Filled circle with outline
        fill_color = QColor(76, 175, 80, alpha // 3)
        painter.setBrush(QBrush(fill_color))
        
        pen = QPen(QColor(76, 175, 80, alpha))
        pen.setWidth(2)
        painter.setPen(pen)
        
        painter.drawEllipse(QPoint(effect.x, effect.y), radius, radius)
    
    def _draw_crosshair(self, painter: QPainter, effect: ClickEffect):
        """Draw a crosshair (+) effect at the click position."""
        alpha = effect.alpha
        size = 8 + int(effect.progress * 12)  # 8px to 20px
        
        pen = QPen(QColor(76, 175, 80, alpha))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Horizontal line
        painter.drawLine(effect.x - size, effect.y, effect.x + size, effect.y)
        # Vertical line
        painter.drawLine(effect.x, effect.y - size, effect.x, effect.y + size)
        
        # Center dot
        painter.setBrush(QBrush(QColor(76, 175, 80, alpha)))
        painter.drawEllipse(QPoint(effect.x, effect.y), 2, 2)
    
    def showEvent(self, event):
        """Handle show - ensure full screen and on top."""
        super().showEvent(event)
        self._update_geometry()
        self.lower()
    
    def closeEvent(self, event):
        """Handle close - clean up all effects."""
        self._cleanup()
        super().closeEvent(event)