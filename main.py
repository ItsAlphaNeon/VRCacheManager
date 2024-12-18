import sys
from PyQt6.QtWidgets import QApplication
from qt_gui_manager import QtGUIManager
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon, QPixmap
import ctypes
from pathlib import Path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Tray Icon
    trayIcon = QSystemTrayIcon(QIcon("./resources/vrcm.ico"), app)
    trayIcon.setToolTip("VRChat Cache Manager")
    trayIcon.show()
    # Taskbar icon
    appid = 'vrcachemanager.vrcm.0.1' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    path_to_icon = './resources/vrcm.ico'
    pixmap = QPixmap()
    pixmap.loadFromData(Path(path_to_icon).read_bytes())
    appIcon = QIcon(pixmap)
    app.setWindowIcon(appIcon)
    
    ex = QtGUIManager()
    ex.show()
    sys.exit(app.exec())
