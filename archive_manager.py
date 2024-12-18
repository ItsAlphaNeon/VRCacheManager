import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QMessageBox,
    QLineEdit,
    QLabel,
    QFileDialog,
    QInputDialog,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from cache_event_handler import CacheEventHandler
from asset_bundle_manager import AssetBundleManager
import recordmanager as RecordManager
from worlddata import get_world_info
from watchdog.observers import Observer
import json
import threading


class ArchiveManager(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the observer
        self.observer = None

        # Initialize the UI
        self.init_ui()

    def start_watching(self, path):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        event_handler = CacheEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        print(f"Watching {path} for changes...")

    def init_ui(self):
        self.setWindowTitle("VRCacheManager")
        self.setGeometry(100, 100, 800, 400)

        main_layout = QHBoxLayout()
        self.record_manager = RecordManager.RecordManager("records.json", "./assetbundles")
        self.record_manager.verify_integrity("assetbundles")
        self.file_list = QListWidget()

        
        worlds = self.record_manager.read_record("Worlds")
        if worlds:
            for world in worlds:
                self.file_list.addItem(f"{world['World Name']} - {world['World Author']}")

        control_layout = QVBoxLayout()

        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.view_btn = QPushButton("View Info")
        self.replace_errorworld_btn = QPushButton("Replace ErrorWorld")

        self.rename_btn.clicked.connect(self.rename_file)
        self.delete_btn.clicked.connect(self.delete_file)
        self.view_btn.clicked.connect(self.view_file_info)
        self.replace_errorworld_btn.clicked.connect(self.replace_errorworld)

        self.vrchat_exec_path = QLineEdit()
        self.vrchat_exec_browse = QPushButton("Browse...")
        self.vrchat_exec_browse.clicked.connect(
            lambda: self.browse_file(self.vrchat_exec_path)
        )

        self.vrchat_cache_path = QLineEdit()
        self.vrchat_cache_browse = QPushButton("Browse...")
        self.vrchat_cache_browse.clicked.connect(
            lambda: self.browse_file(self.vrchat_cache_path)
        )
        
        self.launch_vrchat_btn = QPushButton("Launch VRChat")
        self.launch_vrchat_btn.clicked.connect(self.launch_vrchat)
        
        # Button icons
        self.rename_btn.setIcon(QIcon("./resources/rename_icon.svg"))
        self.delete_btn.setIcon(QIcon("./resources/delete_icon.svg"))
        self.view_btn.setIcon(QIcon("./resources/view_icon.svg"))
        self.replace_errorworld_btn.setIcon(QIcon("./resources/replace_icon.svg"))
        self.vrchat_exec_browse.setIcon(QIcon("./resources/browse_icon.svg"))
        self.vrchat_cache_browse.setIcon(QIcon("./resources/browse_icon.svg"))
        self.launch_vrchat_btn.setIcon(QIcon("./resources/launch_icon.svg"))


        if self.record_manager.verify_record("vrchat_exec"):
            self.vrchat_exec_path.setText(
                self.record_manager.read_record("vrchat_exec")
            )
        if self.record_manager.verify_record("vrchat_cache"):
            self.vrchat_cache_path.setText(
                self.record_manager.read_record("vrchat_cache")
            )
            self.start_watching(self.vrchat_cache_path.text())

        control_layout.addWidget(QLabel("Controls:"))
        control_layout.addWidget(self.rename_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.view_btn)
        control_layout.addWidget(self.replace_errorworld_btn)
        control_layout.addStretch()
        
        control_layout.addWidget(QLabel("<hr>"))
        
        control_layout.addWidget(QLabel("VRChat Executable:"))
        self.vrchat_exec_path.setReadOnly(True)
        control_layout.addWidget(self.vrchat_exec_path)
        control_layout.addWidget(self.vrchat_exec_browse)
        
        control_layout.addWidget(QLabel("<hr>"))
        
        control_layout.addWidget(QLabel("VRChat Cache Directory:"))
        self.vrchat_cache_path.setReadOnly(True)
        control_layout.addWidget(self.vrchat_cache_path)
        control_layout.addWidget(self.vrchat_cache_browse)
        
        control_layout.addWidget(QLabel("<hr>"))
        
        control_layout.addWidget(self.launch_vrchat_btn)

        main_layout.addWidget(self.file_list, 3)
        main_layout.addLayout(control_layout, 1)
        self.setLayout(main_layout)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: None;
            }
            QPushButton {
                background-color: #3A3A3C;
                color: #FFFFFF;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #505052;
            }
            QLineEdit {
                background-color: #3A3A3C;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget {
                background-color: #2D2D30;
                border-radius: 5px;
            }
            QLabel {
                font-weight: bold;
            }
        """
        )

    def rename_file(self):
        selected_item = self.file_list.currentItem()
        if (selected_item):
            new_name, ok = QInputDialog.getText(
                self, "Rename file", "Enter new name:", text=selected_item.text()
            )
            if ok:
                selected_item.setText(new_name)

    def delete_file(self):
        selected_item = self.file_list.currentItem()
        if (selected_item):
            reply = QMessageBox.question(
                self,
                "Delete file",
                "Are you sure you want to delete this file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.file_list.takeItem(self.file_list.row(selected_item))

    def view_file_info(self):
        selected_item = self.file_list.currentItem()
        if (selected_item):
            QMessageBox.information(
                self, "File Info", f"Display Info for {selected_item.text()}"
            )
    
    def replace_errorworld(self):
        if not self.vrchat_cache_path.text():
            QMessageBox.warning(
                self, "Error", "Please specify the path to the VRChat cache directory."
            )
        else:
            # Replace it here!
            QMessageBox.information(
                self, "Placeholder", "This feature is not yet implemented."
            )

    def browse_file(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)
            if line_edit == self.vrchat_cache_path:
                self.start_watching(directory)
                self.record_manager.remove_record("vrchat_cache")
                self.record_manager.add_record("vrchat_cache", directory)
                print("Saved cache path, watching for changes...")
            if line_edit == self.vrchat_exec_path:
                self.record_manager.remove_record("vrchat_exec")
                self.record_manager.add_record("vrchat_exec", directory)
                print("Saved VRChat executable path.")

    def prompt_for_world_url(self, new_data_path):
        url, ok = QInputDialog.getText(
            self, "Enter World URL", "Enter the URL for the newly downloaded world:"
        )
        if ok:
            self.process_world_url(new_data_path, url)
    
    def url_to_id(self, url):
        if "wrld_" in url:
            return "wrld_" + url.split("wrld_")[1]
        else:
            raise ValueError("Invalid URL format")

    def process_world_url(self, new_data_path, url):
        if url:
            try:
                world_info = get_world_info(self.url_to_id(url))
                self.handle_world_info({"world_info": world_info, "new_data_path": new_data_path})
            except Exception as e:
                # we want a stack trace for debugging
                raise e
        else:
            self.handle_error("No URL provided.")

    def handle_world_info(self, data):
        world_info = data["world_info"]
        new_data_path = data["new_data_path"]
        self.record_manager.add_record("Worlds", world_info)
        self.copy_asset_bundle(new_data_path, world_info)
        self.file_list.addItem(f"{world_info['World Name']} - {world_info['World Author']}")

    def copy_asset_bundle(self, new_data_path, world_info):
        try:
            asset_bundle_manager = AssetBundleManager()
            asset_bundle_manager.copy_asset_bundle(new_data_path, "assetbundles", rename=world_info["World ID"])
        except Exception as e:
            self.handle_error(str(e))

    def handle_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def launch_vrchat(self):
        if not self.vrchat_exec_path.text():
            QMessageBox.warning(
                self, "Error", "Please specify the path to the VRChat executable."
            )
        else:
            def launch_vrchat_thread():
                os.system(f'"{self.vrchat_exec_path.text()}/vrchat.exe"')
            threading.Thread(target=launch_vrchat_thread).start()
            print("Launching VRChat...")

    def closeEvent(self, event):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        event.accept() 