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
from pynput import keyboard

from luckyclick.core.hotkey_manager import parse_key_from_string

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

# uinput device structure constants
ABS_CNT = 64  # Maximum number of absolute axes

# Default screen size (fallback if detection fails)
DEFAULT_SCREEN_W = 1920
DEFAULT_SCREEN_H = 1080

CLICK_TYPE_LABELS = {
    'left': 'trái (left)',
    'right': 'phải (right)',
    'middle': 'giữa (middle)',
    'double': 'double click',
}


class VirtualMouse:
    """Virtual mouse device using uinput for non-blocking clicks.
    Uses absolute positioning (EV_ABS) so clicks land exactly at recorded coordinates.
    """

    def __init__(self):
        self.device = None
        self.last_backend = 'unavailable'
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
            
            # Set up uinput_user_dev structure
            # Kernel struct layout:
            #   char name[80]           -> 80s
            #   struct input_id {       -> HHHH (bustype, vendor, product, version)
            #       __u16 bustype
            #       __u16 vendor
            #       __u16 product
            #       __u16 version
            #   }
            #   __u32 ff_effects_max    -> i
            #   __s32 absmax[ABS_CNT]   -> 64i
            #   __s32 absmin[ABS_CNT]   -> 64i
            #   __s32 absfuzz[ABS_CNT]  -> 64i
            #   __s32 absflat[ABS_CNT]  -> 64i
            name = b'LuckyClick Virtual Mouse'
            fmt = '80sHHHHi' + 'i' * ABS_CNT + 'i' * ABS_CNT + 'i' * ABS_CNT + 'i' * ABS_CNT
            
            absmax = [0] * ABS_CNT
            absmin = [0] * ABS_CNT
            absfuzz = [0] * ABS_CNT
            absflat = [0] * ABS_CNT
            
            # Set range for ABS_X and ABS_Y
            absmax[ABS_X] = self.screen_w
            absmax[ABS_Y] = self.screen_h
            # absmin defaults to 0, which is correct for screen coordinates
            
            usetup = struct.pack(
                fmt, name,
                0x0,  # bustype
                0x0,  # vendor
                0x0,  # product
                0x0,  # version
                0,    # ff_effects_max
                *absmax,
                *absmin,
                *absfuzz,
                *absflat
            )
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
            requested_x, requested_y = x, y
            x = max(0, min(x, self.screen_w))
            y = max(0, min(y, self.screen_h))
            if (x, y) != (requested_x, requested_y):
                logger.warning(
                    "uinput position clamped: requested=%d:%d sent=%d:%d screen=%dx%d",
                    requested_x, requested_y, x, y, self.screen_w, self.screen_h
                )
            
            # Write absolute position events
            self._write_event(EV_ABS, ABS_X, x)
            self._write_event(EV_ABS, ABS_Y, y)
            self._syn()
            logger.info(
                "uinput absolute position sent: %d:%d px (screen=%dx%d)",
                x, y, self.screen_w, self.screen_h
            )
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

        # X11 can explicitly warp the desktop pointer; sending EV_ABS alone may
        # be ignored by desktop input stacks even when uinput accepts the event.
        if self._x11_click(x, y, button):
            self.last_backend = 'x11-xtest'
            return

        if self._pynput_click(x, y, button):
            self.last_backend = 'pynput'
            return

        if self.device:
            logger.warning("Desktop pointer APIs unavailable; falling back to uinput")
            self._move_to(x, y)
            time.sleep(0.005)
            self._write_event(EV_KEY, btn_code, 1)
            self._syn()
            time.sleep(0.01)
            self._write_event(EV_KEY, btn_code, 0)
            self._syn()
            self.last_backend = 'uinput'
            return

        self.last_backend = 'unavailable'
        raise RuntimeError("No click backend could move and click the desktop pointer")

    def _x11_click(self, x: int, y: int, button: str):
        """Fallback click using X11 - moves cursor to (x,y) first, then clicks."""
        try:
            from Xlib import X, display
            from Xlib.ext.xtest import fake_input
            
            d = display.Display()
            btn_map = {'left': 1, 'right': 3, 'middle': 2}
            # Move cursor to the recorded position FIRST
            root = d.screen().root
            root.warp_pointer(x, y)
            d.sync()
            pointer = root.query_pointer()
            actual_x, actual_y = int(pointer.root_x), int(pointer.root_y)
            logger.info(
                "X11 pointer after warp: requested=%d:%d actual=%d:%d px",
                x, y, actual_x, actual_y
            )
            if (actual_x, actual_y) != (x, y):
                logger.warning(
                    "X11 pointer did not reach requested position; skipping XTest click"
                )
                d.close()
                return False

            time.sleep(0.01)
            
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
            d.close()
            logger.info(
                "X11 XTest click completed at %d:%d px type=%s",
                x, y, CLICK_TYPE_LABELS.get(button, button)
            )
            return True
        except Exception as e:
            logger.exception("X11 click failed at %d:%d px: %s", x, y, e)
            return False

    def _pynput_click(self, x: int, y: int, button: str):
        """Last resort click using pynput - moves cursor to (x,y) first, then clicks."""
        try:
            from pynput.mouse import Button, Controller
            mouse = Controller()
            logger.info(
                "pynput pointer move: requested=%d:%d px type=%s",
                x, y, CLICK_TYPE_LABELS.get(button, button)
            )
            mouse.position = (x, y)
            time.sleep(0.01)
            actual_x, actual_y = mouse.position
            logger.info(
                "pynput pointer after move: requested=%d:%d actual=%d:%d px",
                x, y, actual_x, actual_y
            )
            if (actual_x, actual_y) != (x, y):
                logger.warning("pynput pointer did not reach requested position")
                return False
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
            logger.info(
                "pynput click completed at %d:%d px type=%s",
                x, y, CLICK_TYPE_LABELS.get(button, button)
            )
            return True
        except Exception as e:
            logger.exception("pynput click failed at %d:%d px: %s", x, y, e)
            return False

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
        self.points: list = []
        self.interval_ms: int = 1000  # milliseconds
        self.click_type: str = 'left'  # Default fallback
        self.max_clicks: int = 0  # 0 = unlimited
        self.random_delay_pct: int = 0  # 0-100
        self.smart_click: bool = False  # If True, use per-point click_type
        self.smart_delay: bool = False  # If True, use per-action delays
        
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

        mode = 'smart' if self.smart_click else 'normal'
        logger.info(
            "Auto clicker configuration: mode=%s points=%d interval_ms=%d "
            "max_clicks=%d global_type=%s backend_priority=X11/pynput/uinput",
            mode, len(self.points), self.interval_ms, self.max_clicks,
            CLICK_TYPE_LABELS.get(self.click_type, self.click_type)
        )

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
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
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

    def _action_interval(self, delay_ms: int) -> float:
        """Resolve the global or per-action delay, including random variation."""
        delay = (
            max(0, int(delay_ms)) / 1000.0
            if self.smart_delay else self.interval_ms / 1000.0
        )
        if self.random_delay_pct > 0:
            import random
            variation = delay * (self.random_delay_pct / 100.0)
            delay = max(0.01, delay + random.uniform(-variation, variation))
        return delay

    def _wait_interval(self, interval: float):
        """Wait for an interval while respecting stop and pause requests."""
        wait_start = time.time()
        while time.time() - wait_start < interval:
            if self._stop_event.is_set():
                break
            if self._pause_event.is_set():
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break
            time.sleep(0.01)

    def _wait_after_action(self, delay_ms: int, action_description: str):
        """Log and apply the configured delay after the completed action."""
        interval = self._action_interval(delay_ms)
        logger.info(
            "Đang delay %.0f ms sau %s...",
            interval * 1000,
            action_description
        )
        self._wait_interval(interval)

    @staticmethod
    def _send_key_action(keys):
        key_objects = []
        for key_name in keys:
            key = parse_key_from_string(key_name)
            if key is None:
                raise ValueError("Unsupported key: {}".format(key_name))
            key_objects.append(key)

        controller = keyboard.Controller()
        pressed_keys = []
        try:
            for key in key_objects:
                controller.press(key)
                pressed_keys.append(key)
        finally:
            for key in reversed(pressed_keys):
                controller.release(key)

    def _click_loop(self):
        """Main click loop running in background thread.
        Checks stop_event AFTER EACH CLICK to ensure immediate stop.
        """
        while not self._stop_event.is_set():
            # Check pause
            if self._pause_event.is_set():
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break
            
            point_count = len(self.points)
            for point_index, point in enumerate(self.points, start=1):
                # Check stop BEFORE each click
                if self._stop_event.is_set():
                    break
                
                if isinstance(point, dict):
                    delay_ms = point.get('delay_ms', 1000)
                    if point.get('type') == 'key':
                        keys = point.get('keys', [])
                        logger.info(
                            "Key action #%d | keys=%s", point_index, '+'.join(keys)
                        )
                        try:
                            self._send_key_action(keys)
                        except Exception:
                            logger.exception(
                                "Key action #%d failed for keys=%s",
                                point_index, '+'.join(keys)
                            )
                        self._wait_after_action(
                            delay_ms,
                            "phím {}".format('+'.join(keys))
                        )
                        continue
                    x, y = point['x'], point['y']
                    point_click_type = point.get('click_type', self.click_type)
                else:
                    delay_ms = 1000
                    if len(point) == 3:
                        x, y, point_click_type = point
                    else:
                        x, y = point[:2]
                        point_click_type = self.click_type
                
                # Use per-point click_type if smart_click is enabled
                actual_click_type = point_click_type if self.smart_click else self.click_type
                click_number = self._click_count + 1
                mode = 'smart' if self.smart_click else 'normal'
                logger.info(
                    "Click #%d | position=%d:%d px | type=%s | mode=%s "
                    "| point=%d/%d",
                    click_number, x, y,
                    CLICK_TYPE_LABELS.get(actual_click_type, actual_click_type),
                    mode, point_index, point_count
                )
                
                try:
                    self.vmouse.click(x, y, actual_click_type)
                    logger.info(
                        "Click #%d completed via backend=%s",
                        click_number, self.vmouse.last_backend
                    )
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
                    logger.exception(
                        "Click #%d failed at %d:%d px: %s", click_number, x, y, e
                    )
                
                self._wait_after_action(
                    delay_ms,
                    "click #{}".format(click_number)
                )
        
        self._running = False

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.vmouse.destroy()