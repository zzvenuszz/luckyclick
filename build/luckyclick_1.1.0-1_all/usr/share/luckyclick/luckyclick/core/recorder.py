"""
Point recorder module for LuckyClick
Handles recording mouse click positions with real-time coordinate tracking.
Supports per-point click type (left, right, double) for smart click mode.
"""

import threading
from typing import Callable, Optional, List, Tuple

# A recorded point: (x, y, click_type)
# click_type is 'left', 'right', 'middle', or 'double'
ClickPoint = Tuple[int, int, str]


class PointRecorder:
    """Records mouse click positions for auto-clicking.
    
    Each point stores (x, y, click_type) to support smart click mode
    where different points can have different click types.
    """

    def __init__(self):
        self._recording = False
        self._thread: Optional[threading.Thread] = None
        self._points: List[ClickPoint] = []
        
        # Callbacks
        self.on_point_recorded: Optional[Callable[[int, int, str], None]] = None
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_coord_update: Optional[Callable[[int, int], None]] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def points(self) -> List[ClickPoint]:
        return self._points.copy()

    def add_point(self, x: int, y: int, click_type: str = 'left'):
        """Manually add a point to the list.
        
        Args:
            x: X coordinate
            y: Y coordinate
            click_type: 'left', 'right', 'middle', or 'double'
        """
        self._points.append((x, y, click_type))
        if self.on_point_recorded:
            self.on_point_recorded(x, y, click_type)

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
        """Replace all points with a new list.
        
        Args:
            points: List of (x, y, click_type) tuples
        """
        self._points = [p if len(p) == 3 else (p[0], p[1], 'left') for p in points]

    def get_points(self) -> List[ClickPoint]:
        """Get all recorded points.
        
        Returns:
            List of (x, y, click_type) tuples
        """
        return self._points.copy()

    def get_points_xy(self) -> List[Tuple[int, int]]:
        """Get points as (x, y) tuples only (backward compatibility).
        
        Returns:
            List of (x, y) tuples
        """
        return [(x, y) for x, y, _ in self._points]

    def load_from_file(self, filepath: str) -> bool:
        """Load points from a JSON file.
        
        Supports both old format [{'x': x, 'y': y}] and new format
        [{'x': x, 'y': y, 'click_type': 'left'}].
        """
        import json
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._points = []
                    for p in data:
                        if 'x' in p and 'y' in p:
                            click_type = p.get('click_type', 'left')
                            self._points.append((p['x'], p['y'], click_type))
                    return True
            return False
        except Exception as e:
            print(f"Error loading points: {e}")
            return False

    def save_to_file(self, filepath: str) -> bool:
        """Save points to a JSON file with click_type."""
        import json
        try:
            data = [{'x': x, 'y': y, 'click_type': t} for x, y, t in self._points]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving points: {e}")
            return False