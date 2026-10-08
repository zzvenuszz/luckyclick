"""
Window Manager detector for LuckyClick.
Detects the current display server and window manager to choose
appropriate overlay window flags for click effects.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Window manager types
WM_X11 = 'x11'
WM_WAYLAND = 'wayland'
WM_UNKNOWN = 'unknown'


def detect_window_manager() -> str:
    """Detect the current window manager / display server.
    
    Checks environment variables in order of reliability:
    1. XDG_SESSION_TYPE (most reliable on modern systems)
    2. WAYLAND_DISPLAY (Wayland-specific)
    3. DISPLAY (X11-specific)
    
    Returns:
        One of WM_X11, WM_WAYLAND, or WM_UNKNOWN
    """
    # Check XDG_SESSION_TYPE first (most reliable)
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    if session_type == 'wayland':
        logger.info("Detected Wayland via XDG_SESSION_TYPE")
        return WM_WAYLAND
    elif session_type == 'x11':
        logger.info("Detected X11 via XDG_SESSION_TYPE")
        return WM_X11
    
    # Check WAYLAND_DISPLAY
    if os.environ.get('WAYLAND_DISPLAY'):
        logger.info("Detected Wayland via WAYLAND_DISPLAY")
        return WM_WAYLAND
    
    # Check DISPLAY (X11)
    if os.environ.get('DISPLAY'):
        logger.info("Detected X11 via DISPLAY")
        return WM_X11
    
    logger.warning("Could not detect window manager, using X11 fallback")
    return WM_X11  # Default to X11 as safest fallback


def get_overlay_window_flags(wm: str) -> dict:
    """Get appropriate window flags and attributes for the detected WM.
    
    Different window managers handle transparent overlays differently:
    - X11: WA_TransparentForMouseEvents works well, avoid X11BypassWindowManagerHint
    - Wayland: May need BypassWindowManagerHint for overlay to appear
    - Unknown: Use safest combination
    
    Args:
        wm: Window manager type from detect_window_manager()
        
    Returns:
        Dict with 'flags' (Qt.WindowFlags) and 'attributes' (list of tuples)
    """
    from PyQt5.QtCore import Qt
    
    base_flags = (
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    
    if wm == WM_WAYLAND:
        # Wayland often needs BypassWindowManagerHint for overlays
        flags = base_flags | Qt.X11BypassWindowManagerHint
        attributes = [
            (Qt.WA_TranslucentBackground, True),
            (Qt.WA_ShowWithoutActivating, True),
            (Qt.WA_TransparentForMouseEvents, True),
            (Qt.WA_DeleteOnClose, True),
        ]
        logger.info("Using Wayland overlay configuration")
    elif wm == WM_X11:
        # X11: avoid BypassWindowManagerHint to prevent mouse blocking
        flags = base_flags
        attributes = [
            (Qt.WA_TranslucentBackground, True),
            (Qt.WA_ShowWithoutActivating, True),
            (Qt.WA_TransparentForMouseEvents, True),
            (Qt.WA_DeleteOnClose, True),
        ]
        logger.info("Using X11 overlay configuration")
    else:
        # Unknown: safest fallback
        flags = base_flags
        attributes = [
            (Qt.WA_TranslucentBackground, True),
            (Qt.WA_ShowWithoutActivating, True),
            (Qt.WA_TransparentForMouseEvents, True),
            (Qt.WA_DeleteOnClose, True),
        ]
        logger.info("Using fallback overlay configuration")
    
    return {'flags': flags, 'attributes': attributes}