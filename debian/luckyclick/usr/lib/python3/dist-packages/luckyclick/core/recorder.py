"""
Point recorder module for LuckyClick
Handles recording mouse click positions with real-time coordinate tracking.
Supports per-point click type (left, right, double) for smart click mode.
"""

import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

# Click actions contain coordinates and click_type; key actions contain keys.
ClickPoint = Dict[str, Any]


class PointRecorder:
    """Records mouse click positions for auto-clicking.
    
    Each action stores its type and delay, plus coordinates or captured keys.
    """

    def __init__(self):
        self._recording = False
        self._thread: Optional[threading.Thread] = None
        self._points: List[ClickPoint] = []
        
        # Callbacks
        self.on_point_recorded: Optional[Callable[[ClickPoint], None]] = None
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_coord_update: Optional[Callable[[int, int], None]] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def points(self) -> List[ClickPoint]:
        return self.get_points()

    def add_point(self, x: int, y: int, click_type: str = 'left'):
        """Manually add a point to the list.
        
        Args:
            x: X coordinate
            y: Y coordinate
            click_type: 'left', 'right', 'middle', or 'double'
        """
        point = {
            'type': 'click',
            'x': x,
            'y': y,
            'click_type': click_type,
            'delay_ms': 1000,
        }
        self._points.append(point)
        if self.on_point_recorded:
            self.on_point_recorded(point.copy())

    def add_key_action(self, keys: List[str]):
        """Add a keyboard action to the sequence."""
        point = {'type': 'key', 'keys': keys.copy(), 'delay_ms': 1000}
        self._points.append(point)
        if self.on_point_recorded:
            self.on_point_recorded(point.copy())

    def set_delay(self, index: int, delay_ms: int) -> bool:
        """Set an action's delay in milliseconds."""
        if not 0 <= index < len(self._points):
            return False
        self._points[index]['delay_ms'] = max(0, int(delay_ms))
        return True

    def remove_point(self, index: int) -> bool:
        """Remove a point by index. Returns True if successful."""
        if 0 <= index < len(self._points):
            self._points.pop(index)
            return True
        return False

    def clear_points(self):
        """Clear all recorded points."""
        self._points.clear()

    def set_points(self, points: List[ClickPoint]):
        """Replace points, upgrading legacy point tuples and profile entries."""
        normalized = []
        for point in points:
            if isinstance(point, dict):
                action_type = point.get('type', 'click')
                delay_ms = max(0, int(point.get('delay_ms', 1000)))
                if action_type == 'key':
                    keys = point.get('keys', [])
                    if isinstance(keys, str):
                        keys = keys.split('+')
                    normalized.append({
                        'type': 'key',
                        'keys': [str(key) for key in keys],
                        'delay_ms': delay_ms,
                    })
                elif 'x' in point and 'y' in point:
                    normalized.append({
                        'type': 'click',
                        'x': int(point['x']),
                        'y': int(point['y']),
                        'click_type': point.get('click_type', 'left'),
                        'delay_ms': delay_ms,
                    })
            elif len(point) >= 2:
                normalized.append({
                    'type': 'click',
                    'x': int(point[0]),
                    'y': int(point[1]),
                    'click_type': point[2] if len(point) >= 3 else 'left',
                    'delay_ms': int(point[3]) if len(point) >= 4 else 1000,
                })
        self._points = normalized

    def get_points(self) -> List[ClickPoint]:
        """Get all recorded points.
        
        Returns:
            A list of normalized action dictionaries
        """
        return [
            dict(point, **({'keys': point['keys'].copy()} if point['type'] == 'key' else {}))
            for point in self._points
        ]

    def get_points_xy(self) -> List[Tuple[int, int]]:
        """Get points as (x, y) tuples only (backward compatibility).
        
        Returns:
            List of (x, y) tuples
        """
        return [
            (point['x'], point['y'])
            for point in self._points
            if point['type'] == 'click'
        ]

    def load_from_file(self, filepath: str) -> bool:
        """Load points from a JSON file.
        
        Supports old click point formats and the current click/key action format.
        """
        import json
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._points = []
                    self.set_points(data)
                    return True
            return False
        except Exception as e:
            print(f"Error loading points: {e}")
            return False

    def save_to_file(self, filepath: str) -> bool:
        """Save click and key actions to a JSON file."""
        import json
        try:
            data = self.get_points()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving points: {e}")
            return False