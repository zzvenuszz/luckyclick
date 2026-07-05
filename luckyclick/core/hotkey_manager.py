"""
Global hotkey manager for LuckyClick
Uses pynput keyboard listener on a separate thread for reliable hotkey detection.
Supports custom key capture for user-defined hotkeys.
"""

import threading
import logging
from typing import Callable, Optional, Dict, Any
from pynput import keyboard

logger = logging.getLogger(__name__)

# Key mapping for display names to pynput keys
KEY_MAP = {
    'F1': keyboard.Key.f1,
    'F2': keyboard.Key.f2,
    'F3': keyboard.Key.f3,
    'F4': keyboard.Key.f4,
    'F5': keyboard.Key.f5,
    'F6': keyboard.Key.f6,
    'F7': keyboard.Key.f7,
    'F8': keyboard.Key.f8,
    'F9': keyboard.Key.f9,
    'F10': keyboard.Key.f10,
    'F11': keyboard.Key.f11,
    'F12': keyboard.Key.f12,
    'Insert': keyboard.Key.insert,
    'Home': keyboard.Key.home,
    'End': keyboard.Key.end,
    'PageUp': keyboard.Key.page_up,
    'PageDown': keyboard.Key.page_down,
    'ScrollLock': keyboard.Key.scroll_lock,
    'Pause': keyboard.Key.pause,
    'PrintScreen': keyboard.Key.print_screen,
    'Menu': keyboard.Key.menu,
}

# Reverse map for display
KEY_NAMES = {v: k for k, v in KEY_MAP.items()}

# Available hotkeys for dropdown (keys that rarely conflict with OS)
AVAILABLE_HOTKEYS = [
    'F4', 'F8', 'F9', 'F10', 'F11', 'F12',
    'Insert', 'Home', 'End', 'PageUp', 'PageDown',
    'ScrollLock', 'Pause', 'PrintScreen', 'Menu',
    'Tùy chỉnh (Custom)'
]


def key_to_string(key) -> Optional[str]:
    """Convert a pynput key to a display string.
    
    Handles both special keys (Key.f1, etc.) and alphanumeric keys.
    
    Args:
        key: pynput key object (Key or KeyCode)
        
    Returns:
        String representation, or None if conversion fails
    """
    if hasattr(key, 'name'):
        # Special key (F1-F12, etc.)
        name = key.name
        # Capitalize first letter for consistency
        if name.startswith('f') and name[1:].isdigit():
            return name.upper()
        # CamelCase for multi-word names
        return ''.join(word.capitalize() for word in name.split('_'))
    elif hasattr(key, 'char'):
        # Character key
        char = key.char
        if char is not None:
            return char.upper()
    return None


def parse_key_from_string(key_str: str):
    """Convert a string back to a pynput key object.
    
    Handles both predefined keys (F1-F12, etc.) and custom keys.
    
    Args:
        key_str: String representation of the key
        
    Returns:
        pynput key object, or None if not recognized
    """
    # Check predefined keys first
    if key_str in KEY_MAP:
        return KEY_MAP[key_str]
    
    # Handle single character keys
    if len(key_str) == 1 and key_str.isprintable():
        return keyboard.KeyCode.from_char(key_str.lower())
    
    # Handle special named keys not in KEY_MAP
    special_names = {
        'Space': keyboard.Key.space,
        'Enter': keyboard.Key.enter,
        'Tab': keyboard.Key.tab,
        'Escape': keyboard.Key.esc,
        'Backspace': keyboard.Key.backspace,
        'Delete': keyboard.Key.delete,
        'Shift': keyboard.Key.shift,
        'Ctrl': keyboard.Key.ctrl,
        'Alt': keyboard.Key.alt,
        'Up': keyboard.Key.up,
        'Down': keyboard.Key.down,
        'Left': keyboard.Key.left,
        'Right': keyboard.Key.right,
    }
    if key_str in special_names:
        return special_names[key_str]
    
    return None


class HotkeyManager:
    """Manages global hotkeys using pynput keyboard listener."""

    def __init__(self):
        self._listener: Optional[keyboard.Listener] = None
        self._hotkeys: Dict[keyboard.Key, Callable] = {}
        self._running = False
        self._lock = threading.Lock()
        
        # Custom key capture state
        self._capturing = False
        self._capture_callback: Optional[Callable[[str], None]] = None

    def register_hotkey(self, key_name: str, callback: Callable) -> bool:
        """Register a hotkey with a callback function.
        
        Args:
            key_name: Display name of the key (e.g., 'F4', 'F8', 'A', 'Space')
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registered successfully
        """
        key = parse_key_from_string(key_name)
        if key is None:
            logger.error(f"Unknown key: {key_name}")
            return False
        
        with self._lock:
            # Remove any existing registration for the same key to avoid duplicates
            existing_keys = [k for k, v in self._hotkeys.items() if v == callback]
            for ek in existing_keys:
                del self._hotkeys[ek]
            self._hotkeys[key] = callback
        logger.info(f"Registered hotkey: {key_name}")
        return True

    def unregister_hotkey(self, key_name: str):
        """Unregister a hotkey by name."""
        key = parse_key_from_string(key_name)
        if key:
            with self._lock:
                self._hotkeys.pop(key, None)
                logger.info(f"Unregistered hotkey: {key_name}")

    def start_capture(self, callback: Callable[[str], None]):
        """Start capturing the next key press as a custom hotkey.
        
        Args:
            callback: Function to call with the captured key name string
        """
        with self._lock:
            self._capturing = True
            self._capture_callback = callback
        logger.info("Started custom hotkey capture")

    def cancel_capture(self):
        """Cancel ongoing key capture."""
        with self._lock:
            self._capturing = False
            self._capture_callback = None
        logger.info("Cancelled custom hotkey capture")

    def start(self):
        """Start the keyboard listener on a separate thread."""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started")

    def stop(self):
        """Stop the keyboard listener."""
        self._running = False
        self._capturing = False
        self._capture_callback = None
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("Hotkey listener stopped")

    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Check for custom key capture mode first
            with self._lock:
                if self._capturing and self._capture_callback:
                    key_str = key_to_string(key)
                    if key_str:
                        self._capturing = False
                        cb = self._capture_callback
                        self._capture_callback = None
                        # Run callback in separate thread
                        threading.Thread(target=cb, args=(key_str,), daemon=True).start()
                        return
            
            # Normal hotkey dispatch
            with self._lock:
                if key in self._hotkeys:
                    callback = self._hotkeys[key]
                    # Run callback in a separate thread to avoid blocking
                    threading.Thread(target=callback, daemon=True).start()
        except Exception as e:
            logger.error(f"Hotkey handler error: {e}")

    @staticmethod
    def get_available_keys() -> list:
        """Get list of available hotkey names for UI dropdown."""
        return AVAILABLE_HOTKEYS.copy()