"""
Standalone script to generate LuckyClick icon PNGs.
This runs without needing a display server.
"""
import sys
import os

# Force offscreen mode
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF


def create_clover_icon(size: int = 64) -> QPixmap:
    """Create a four-leaf clover icon programmatically."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    center = QPointF(size / 2, size / 2)
    leaf_size = size * 0.35
    stem_length = size * 0.2
    
    dark_green = QColor(34, 139, 34)
    light_green = QColor(76, 175, 80)
    stem_color = QColor(27, 94, 32)
    
    # Draw stem
    stem_path = QPainterPath()
    stem_path.moveTo(center.x(), center.y() + 2)
    stem_path.quadTo(
        center.x() + 3, center.y() + stem_length + 5,
        center.x(), center.y() + stem_length + 10
    )
    pen = QPen(stem_color, max(2, size // 20))
    painter.strokePath(stem_path, pen)
    
    # Draw 4 leaves
    angles = [-45, 45, 135, 225]
    
    for angle in angles:
        painter.save()
        painter.translate(center)
        painter.rotate(angle)
        
        # Leaf shape (heart-like)
        leaf = QPainterPath()
        leaf.moveTo(0, 0)
        leaf.cubicTo(leaf_size * 0.5, -leaf_size * 0.3,
                     leaf_size * 0.8, -leaf_size * 0.7,
                     0, -leaf_size * 1.1)
        leaf.cubicTo(-leaf_size * 0.8, -leaf_size * 0.7,
                     -leaf_size * 0.5, -leaf_size * 0.3,
                     0, 0)
        
        painter.fillPath(leaf, QBrush(light_green if angle % 90 == 45 else dark_green))
        painter.setPen(QPen(QColor(27, 94, 32), max(1, size // 40)))
        painter.drawPath(leaf)
        
        painter.restore()
    
    # Draw center dot
    painter.setBrush(QBrush(stem_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(center, size * 0.06, size * 0.06)
    
    painter.end()
    return pixmap


def main():
    resource_dir = os.path.join(os.path.dirname(__file__), 'luckyclick', 'resources', 'icons')
    os.makedirs(resource_dir, exist_ok=True)
    
    sizes = [16, 32, 48, 64, 128, 256]
    for size in sizes:
        pixmap = create_clover_icon(size)
        filepath = os.path.join(resource_dir, f'luckyclick_{size}.png')
        pixmap.save(filepath, 'PNG')
        print(f"  Created: {filepath} ({size}x{size})")
    
    # Main icon (256px)
    pixmap = create_clover_icon(256)
    filepath = os.path.join(resource_dir, 'luckyclick.png')
    pixmap.save(filepath, 'PNG')
    print(f"  Created: {filepath} (256x256, main)")
    
    print("\n✅ All icons generated successfully!")


if __name__ == '__main__':
    main()