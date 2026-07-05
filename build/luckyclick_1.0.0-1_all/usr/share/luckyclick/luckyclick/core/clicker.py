"""
Click engine for LuckyClick
Supports left, right, middle, and double click using uinput (virtual device)
for non-blocking click functionality.

Uses absolute positioning (EV_ABS) for accurate clicks at recorded coordinates.
"""

import threading
import time
import struct
import fcntl
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# uinput constants
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_RELBIT = 0x40045566
UI_SET_ABSBIT = 0x40045567
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

# Event types
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03

# Relative axes
REL_X = 0x00
REL_Y = 0x01

# Absolute axes
ABS_X = 0x00
ABS_Y = 0x01

# Button codes (from linux/input-event-codes.h)
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112

# uinput device structure
UI_DEV_SETUP_STRUCT = '80sHHHi'  # name, id, etc.

# Default screen size (fallback if detection fails)
DEFAULT_SCREEN_W = 1920
DEFAULT_SCREEN_H = 1080


class VirtualMouse:
    """Virtual mouse device using uinput for non-blocking clicks.
    Uses absolute positioning (EV_ABS) so clicks land exactly at recorded coordinates.
    """

    def __init__(self):
        self.device = None
        self.screen_w = DEFAULT_SCREEN_W
        self.screen_h = DEFAULT_SCREEN_H
        self._detect_screen()
        self._setup_device()

    def _detect_screen(self):
        """Detect screen dimensions from environment if possible."""
        try:
            # Try using X11
            import subprocess
            result = subprocess.run(
                ['xrandr', '--current'],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if ' connected' in line or '*' in line:
                    import re
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        self.screen_w = int(match.group(1))
                        self.screen_h = int(match.group(2))
                        logger.info(f"Detected screen: {self.screen_w}x{self.screen_h}")
                        return
        except Exception:
            pass

        # Fallback: try reading /sys/class/graphics/fb0/virtual_size
        try:
            with open('/sys/class/graphics/fb0/virtual_size', 'r') as f:
                data = f.read().strip().split(',')
                if len(data) == 2:
                    self.screen_w = int(data[0])
                    self.screen_h = int(data[1])
                    logger.info(f"Screen from fb0: {self.screen_w}x{self.screen_h}")
                    return
        except Exception:
            pass

        logger.warning(f"Could not detect screen, using default {self.screen_w}x{self.screen_h}")

    def _setup_device(self):
        """Create a uinput virtual mouse device with absolute positioning support."""
        try:
            self.device = open('/dev/uinput', 'wb', buffering=0)
            
            # Enable event types
            fcntl.ioctl(self.device, UI_SET_EVBIT, EV_KEY)
            fcntl.ioctl(self.device, UI_SET_EVBIT, EV_ABS)
            fcntl.ioctl(self.device, UI_SET_EVBIT, EV_REL)  # Keep REL as fallback
            
            # Enable absolute axes (for precise positioning)
            fcntl.ioctl(self.device, UI_SET_ABSBIT, ABS_X)
            fcntl.ioctl(self.device, UI_SET_ABSBIT, ABS_Y)
            
            # Enable relative events (fallback for cursor movement)
            fcntl.ioctl(self.device, UI_SET_RELBIT, REL_X)
            fcntl.ioctl(self.device, UI_SET_RELBIT, REL_Y)
            
            # Enable button events
            fcntl.ioctl(self.device, UI_SET_KEYBIT, BTN_LEFT)
            fcntl.ioctl(self.device, UI_SET_KEYBIT, BTN_RIGHT)
            fcntl.ioctl(self.device, UI_SET_KEYBIT, BTN_MIDDLE)
            
            # Set up device structure
            name = b'LuckyClick Virtual Mouse'
            usetup = struct.pack('80sHHHi', name, 0x0, 0x0, 0x0, 0x0)
            self.device.write(usetup)
            
            # Create device
            fcntl.ioctl(self.device, UI_DEV_CREATE)
            
            logger.info(f"Virtual mouse device created (screen: {self.screen_w}x{self.screen_h})")
            
        except Exception as e:
            logger.error(f"Failed to create virtual mouse: {e}")
            logger.warning("Falling back to X11 simulation")
            self.device = None

    def _write_event(self, ev_type, code, value):
        """Write an input event to the device."""
        if self.device is None:
            return
        event = struct.pack('llHHI', 0, 0, ev_type, code, value)
        self.device.write(event)

    def _syn(self):
        """Synchronize events."""
        self._write_event(EV_SYN, 0, 0)

    def _move_to(self, x: int, y: int):
        """Move cursor to absolute coordinates using EV_ABS.
        
        Args:
            x: Target X coordinate (physical pixels)
            y: Target Y coordinate (physical pixels)
        """
        if self.device:
            # Clamp coordinates to screen bounds
            x = max(0, min(x, self.screen_w))
            y = max(0, min(y, self.screen_h))
            
            # Write absolute position events
            self._write_event(EV_ABS, ABS_X, x)
            self._write_event(EV_ABS, ABS_Y, y)
            self._syn()
            time.sleep(0.005)  # Small delay to ensure position is registered

    def click(self, x: int, y: int, button: str = 'left'):
        """Perform a click at the specified position using the virtual device.
        
        First moves cursor to the exact (x, y) coordinates using absolute positioning,
        then performs the click. This ensures clicks land exactly where recorded.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: 'left', 'right', 'middle', or 'double'
        """
        if button == 'double':
            self.click(x, y, 'left')
            self.click(x, y, 'left')
            return

        btn_code = {
            'left': BTN_LEFT,
            'right': BTN_RIGHT,
            'middle': BTN_MIDDLE
        }.get(button, BTN_LEFT)

        # Click using virtual device (does not steal real mouse)
        if self.device:
            # Move to exact position FIRST
            self._move_to(x, y)
            time.sleep(0.005)
            
            # Press and release
            self._write_event(EV_KEY, btn_code, 1)  # Press
            self._syn()
            time.sleep(0.01)
            self._write_event(EV_KEY, btn_code, 0)  # Release
            self._syn()
        else:
            # Fallback: use Xlib
            self._x11_click(x, y, button)

    def _x11_click(self, x: int, y: int, button: str):
        """Fallback click using X11 (no MotionNotify - does NOT move real mouse)."""
        try:
            from Xlib import X, display
            from Xlib.ext.xtest import fake_input
            
            d = display.Display()
            btn_map = {'left': 1, 'right': 3, 'middle': 2}
            
            btn = btn_map.get(button, 1)
            if button == 'double':
                fake_input(d, X.ButtonPress, btn)
                fake_input(d, X.ButtonRelease, btn)
                fake_input(d, X.ButtonPress, btn)
                fake_input(d, X.ButtonRelease, btn)
            else:
                fake_input(d, X.ButtonPress, btn)
                fake_input(d, X.ButtonRelease, btn)
            d.sync()
        except Exception as e:
            logger.error(f"X11 click fallback failed: {e}")
            # Last resort: pynput
            self._pynput_click(x, y, button)

    def _pynput_click(self, x: int, y: int, button: str):
        """Last resort click using pynput."""
        try:
            from pynput.mouse import Button, Controller
            mouse = Controller()
            mouse.position = (x, y)
            btn_map = {
                'left': Button.left,
                'right': Button.right,
                'middle': Button.middle,
                'double': Button.left
            }
            btn = btn_map.get(button, Button.left)
            if button == 'double':
                mouse.click(btn, 2)
            else:
                mouse.click(btn, 1)
        except Exception as e:
            logger.error(f"pynput click failed: {e}")

    def destroy(self):
        """Destroy the virtual device."""
        if self.device:
            try:
                fcntl.ioctl(self.device, UI_DEV_DESTROY)
                self.device.close()
                logger.info("Virtual mouse device destroyed")
            except Exception as e:
                logger.error(f"Failed to destroy virtual mouse: {e}")


class AutoClicker:
    """Auto click engine that runs in a separate thread."""

    def __init__(self):
        self.vmouse = VirtualMouse()
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Configuration
        self.points: list[tuple[int, int, str]] = []  # (x, y, click_type)
        self.interval_ms: int = 1000  # milliseconds
        self.click_type: str = 'left'  # Default fallback
        self.max_clicks: int = 0  # 0 = unlimited
        self.random_delay_pct: int = 0  # 0-100
        self.smart_click: bool = False  # If True, use per-point click_type
        
        # Callbacks
        self.on_click: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.on_finished: Optional[Callable] = None
        
        self._click_count = 0

    @property
    def is_running(self) -> bool:
        return self._running and not self._stop_event.is_set()

    @property
    def click_count(self) -> int:
        return self._click_count

    def start(self):
        """Start auto clicking in a background thread."""
        if self._running:
            return
        
        if not self.points:
            logger.warning("No click points defined")
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self._click_count = 0
        self._running = True
        
        self._thread = threading.Thread(target=self._click_loop, daemon=True)
        self._thread.start()
        logger.info("Auto clicker started")

    def stop(self):
        """Stop auto clicking. Thread-safe."""
        self._stop_event.set()
        self._running = False
        if self.on_stop:
            self.on_stop()
        logger.info("Auto clicker stopped")

    def pause(self):
        """Pause auto clicking."""
        self._paused = True
        self._pause_event.set()
        logger.info("Auto clicker paused")

    def resume(self):
        """Resume auto clicking."""
        self._paused = False
        self._pause_event.clear()
        logger.info("Auto clicker resumed")

    def _click_loop(self):
        """Main click loop running in background thread.
        Checks stop_event AFTER EACH CLICK to ensure immediate stop.
        """
        interval_sec = self.interval_ms / 1000.0
        
        while not self._stop_event.is_set():
            # Check pause
            if self._pause_event.is_set():
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break
            
            for point in self.points:
                # Check stop BEFORE each click
                if self._stop_event.is_set():
                    break
                
                # Unpack point - supports both (x, y) and (x, y, click_type)
                if len(point) == 3:
                    x, y, point_click_type = point
                else:
                    x, y = point[:2]
                    point_click_type = self.click_type
                
                # Use per-point click_type if smart_click is enabled
                actual_click_type = point_click_type if self.smart_click else self.click_type
                
                try:
                    self.vmouse.click(x, y, actual_click_type)
                    self._click_count += 1
                    
                    if self.on_click:
                        self.on_click(x, y, self._click_count)
                    
                    # Check max clicks
                    if self.max_clicks > 0 and self._click_count >= self.max_clicks:
                        logger.info(f"Reached max clicks: {self.max_clicks}")
                        self._stop_event.set()
                        if self.on_finished:
                            self.on_finished()
                        break
                    
                except Exception as e:
                    logger.error(f"Click error: {e}")
                
                # Apply random delay if configured
                actual_interval = interval_sec
                if self.random_delay_pct > 0:
                    import random
                    variation = actual_interval * (self.random_delay_pct / 100.0)
                    actual_interval += random.uniform(-variation, variation)
                    actual_interval = max(0.01, actual_interval)
                
                # Wait interval - but check stop_event frequently
                wait_start = time.time()
                while time.time() - wait_start < actual_interval:
                    if self._stop_event.is_set():
                        break
                    if self._pause_event.is_set():
                        self._pause_event.wait()
                        if self._stop_event.is_set():
                            break
                    time.sleep(0.01)  # Check every 10ms
        
        self._running = False
        logger.info("Click loop ended")

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.vmouse.destroy()