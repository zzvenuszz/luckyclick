"""
LuckyClick - Auto Clicker for Linux
Main entry point
"""

import sys
import os
import logging
import signal

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSharedMemory

from luckyclick.gui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/.luckyclick.log'), mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Unique key for single-instance detection
SHARED_MEMORY_KEY = 'LuckyClick-SingleInstance-42f3a1b8'
PID_FILE = os.path.expanduser('~/.luckyclick.pid')


def bring_existing_window_to_front():
    """Try to bring the existing LuckyClick window to front.
    
    Reads the PID from the PID file and sends SIGUSR1 signal.
    The running instance handles this signal to show/raise its window.
    """
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            # Check if process with that PID still exists
            if os.path.exists(f'/proc/{old_pid}'):
                os.kill(old_pid, signal.SIGUSR1)
                logger.info(f"Sent SIGUSR1 to existing instance (PID: {old_pid})")
                return True
    except (ValueError, OSError, ProcessLookupError) as e:
        logger.warning(f"Could not bring existing window to front: {e}")
    return False


def main():
    """Main entry point."""
    # Handle SIGINT (Ctrl+C) gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("LuckyClick")
    app.setApplicationDisplayName("LuckyClick - Auto Clicker")
    app.setOrganizationName("LuckyClick")
    app.setQuitOnLastWindowClosed(False)
    
    # === Single instance check using QSharedMemory ===
    shared_mem = QSharedMemory(SHARED_MEMORY_KEY)
    
    # Try to create shared memory segment
    if not shared_mem.create(1):
        # Creation failed - check if another instance is running
        if shared_mem.error() == QSharedMemory.AlreadyExists:
            logger.warning("Another instance of LuckyClick is already running")
            
            # Try to attach to existing segment
            if shared_mem.attach():
                # Check PID file to see if the process is still alive
                old_pid = None
                try:
                    if os.path.exists(PID_FILE):
                        with open(PID_FILE, 'r') as f:
                            old_pid = int(f.read().strip())
                except (ValueError, OSError) as e:
                    logger.warning(f"Could not read PID file: {e}")
                
                # Check if the old process is still running
                if old_pid and os.path.exists(f'/proc/{old_pid}'):
                    # Another instance is actually running - bring it to front
                    bring_existing_window_to_front()
                    QMessageBox.information(
                        None,
                        "LuckyClick",
                        "LuckyClick đã chạy rồi!\n(LuckyClick is already running!)\n\nĐã mở cửa sổ ứng dụng."
                    )
                    shared_mem.detach()
                    sys.exit(1)
                else:
                    # Old process is dead - orphaned shared memory
                    # Clean up and continue
                    logger.info("Found orphaned shared memory, cleaning up...")
                    shared_mem.detach()
                    
                    # Try to create again
                    if not shared_mem.create(1):
                        logger.error(f"Failed to create shared memory after cleanup: {shared_mem.errorString()}")
                        QMessageBox.warning(
                            None,
                            "LuckyClick",
                            "Không thể khởi động LuckyClick.\n(Cannot start LuckyClick)"
                        )
                        sys.exit(1)
            else:
                # Cannot attach - something is wrong
                logger.error(f"Cannot attach to shared memory: {shared_mem.errorString()}")
                QMessageBox.warning(
                    None,
                    "LuckyClick",
                    "Không thể khởi động LuckyClick.\n(Cannot start LuckyClick)"
                )
                sys.exit(1)
        else:
            # Some other error
            logger.error(f"Failed to create shared memory: {shared_mem.errorString()}")
            QMessageBox.warning(
                None,
                "LuckyClick",
                f"Không thể khởi động LuckyClick.\n(Cannot start LuckyClick)\n\nError: {shared_mem.errorString()}"
            )
            sys.exit(1)
    
    # Write PID file
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Wrote PID file: {PID_FILE}")
    except Exception as e:
        logger.warning(f"Could not write PID file: {e}")
    
    # Load application icon (icon is pre-installed by .deb, no runtime generation needed)
    icon_path = get_icon_path()
    if icon_path:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        logger.info("Loaded icon from %s", icon_path)
    else:
        # Try theme icon
        app_icon = QIcon.fromTheme('luckyclick')
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
            logger.info("Loaded icon from theme")
        else:
            app_icon = QIcon()
            logger.warning("No icon found")
    
    # Create and show main window
    window = MainWindow()
    if not app_icon.isNull():
        window.set_app_icon(app_icon)
    window.show()
    
    # Register SIGUSR1 handler to bring window to front
    def sigusr1_handler(signum, frame):
        """Handle SIGUSR1 - bring window to front."""
        logger.info("Received SIGUSR1, bringing window to front")
        window.show()
        window.raise_()
        window.activateWindow()
    
    signal.signal(signal.SIGUSR1, sigusr1_handler)
    
    logger.info("LuckyClick started")
    
    # Run app
    exit_code = app.exec_()
    
    # Clean up shared memory and PID file on exit
    if shared_mem.isAttached():
        shared_mem.detach()
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logger.info("Removed PID file")
    except Exception as e:
        logger.warning(f"Could not remove PID file: {e}")
    
    sys.exit(exit_code)


def get_icon_path() -> str:
    """Get the path to the application icon.
    
    Search order:
    1. System icon from .deb install (theme icon)
    2. Local development copy
    3. Fallback to empty
    """
    # The icon is installed to /usr/share/icons/hicolor/... by .deb package
    # and referenced by name 'luckyclick' in .desktop file.
    # For QIcon.fromTheme to work, the icon must be in hicolor theme.
    
    # Try direct path first (most reliable)
    paths = [
        '/usr/share/icons/hicolor/256x256/apps/luckyclick.png',
        os.path.join(os.path.dirname(__file__), 'icon.png'),
        os.path.join(os.path.dirname(__file__), 'resources', 'icons', 'luckyclick.png'),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    
    # Try theme fallback
    if QIcon.hasThemeIcon('luckyclick'):
        return ''
    
    return ''


if __name__ == '__main__':
    main()