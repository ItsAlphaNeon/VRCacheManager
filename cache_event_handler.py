from watchdog.events import FileSystemEventHandler

from PyQt6.QtCore import QObject, pyqtSignal

class CacheEventHandler(FileSystemEventHandler, QObject):
    fileCreated = pyqtSignal(str)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.fileCreated.connect(manager.discover_existing_cache)

    def on_created(self, event):
        if event.is_directory:
            return
        if "__data" in event.src_path:
            self.fileCreated.emit(event.src_path)
