import os
import sys
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
    QApplication,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap
from cache_event_handler import CacheEventHandler
from asset_bundle_manager import AssetBundleManager
import record_manager as RecordManager
from worlddata import get_world_info
from watchdog.observers import Observer
import json
import threading
import shutil


class ListItemWidget(QWidget):
    def __init__(self, thumbnail_path, world_name, world_author, world_id, parent=None):
        super(ListItemWidget, self).__init__(parent)
        self.world_id = world_id  # Assign the world ID

        layout = QHBoxLayout(self)

        # Create and configure the thumbnail label
        thumbnail_label = QLabel(self)
        thumbnail_label.setPixmap(
            QPixmap(thumbnail_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
        )

        # Create and configure the text label
        text_label = QLabel(self)
        text_label.setText(f"{world_name} - {world_author}")
        text_label.setStyleSheet("color: #FFFFFF; margin: 10px;")

        # Add widgets to layout
        layout.addWidget(thumbnail_label)
        layout.addWidget(text_label)

        layout.setContentsMargins(5, 5, 5, 5)
        layout.addStretch()


class QtGUIManager(QWidget):
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
        self.record_manager = RecordManager.RecordManager(
            "records.json", "./assetbundles"
        )
        self.record_manager.verify_integrity("assetbundles")
        self.file_list = QListWidget()

        worlds = self.record_manager.read_record("Worlds")
        if worlds:
            for world in worlds:
                thumbnail_path = world.get(
                    "Thumbnail Path", "./resources/default_thumbnail.png"
                )
                world_name = world.get("World Name", "Unknown")
                world_author = world.get("World Author", "Unknown")

                list_item_widget = ListItemWidget(
                    thumbnail_path, world_name, world_author, world["World ID"]
                )
                list_item = QListWidgetItem(self.file_list)
                list_item.setSizeHint(list_item_widget.sizeHint())

                list_item.world_id = world["World ID"]

                # Add the item and set the widget within the loop
                self.file_list.addItem(list_item)
                self.file_list.setItemWidget(list_item, list_item_widget)

        # Add additional logic or widgets to your UI layout here
        main_layout.addWidget(self.file_list)
        self.setLayout(main_layout)

        control_layout = QVBoxLayout()
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.view_btn = QPushButton("View Info")
        self.replace_errorworld_btn = QPushButton("Replace ErrorWorld")

        self.rename_btn.setToolTip("Rename the selected world")
        self.delete_btn.setToolTip("Delete the selected world")
        self.view_btn.setToolTip("View information about the selected world")
        self.replace_errorworld_btn.setToolTip(
            "Replace the error world with the selected world"
        )

        self.rename_btn.clicked.connect(lambda: self.rename_file(self.record_manager))
        self.delete_btn.clicked.connect(self.delete_file)
        self.view_btn.clicked.connect(self.view_file_info)
        self.replace_errorworld_btn.clicked.connect(self.replace_errorworld)

        self.vrchat_exec_path = QLineEdit()
        self.vrchat_exec_browse = QPushButton("Browse...")
        self.vrchat_exec_browse.setToolTip("Browse for the VRChat executable path")
        self.vrchat_exec_browse.clicked.connect(
            lambda: self.browse_file(self.vrchat_exec_path)
        )

        self.vrchat_cache_path = QLineEdit()
        self.vrchat_cache_browse = QPushButton("Browse...")
        self.vrchat_cache_browse.setToolTip("Browse for the VRChat cache directory")
        self.vrchat_cache_browse.clicked.connect(
            lambda: self.browse_file(self.vrchat_cache_path)
        )

        self.launch_vrchat_btn = QPushButton("Launch VRChat")
        self.launch_vrchat_btn.setToolTip("Launch VRChat application")
        self.launch_vrchat_btn.clicked.connect(self.launch_vrchat)

        # Disable the launch button if the platform is macOS or Linux
        if sys.platform == "win32":
            self.launch_vrchat_btn.setEnabled(True)
        else:
            self.launch_vrchat_btn.setEnabled(False)
            self.launch_vrchat_btn.setToolTip(
                "Launching VRChat is only supported on Windows"
            )

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
            QPushButton:disabled {
            background-color: #5A5A5C;
            color: #888888;
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
            QListWidget::item {
            background-color: transparent;  /* Use transparent to avoid conflicting effects */
            color: #CCCCCC;
            }
            QListWidget::item:selected {
            background-color: #505052;  /* Highlight color */
            color: #FFFFFF;
            }
            QLabel {
            font-weight: bold;
            background-color: transparent;  /* Ensure QLabel has no explicit color */
            }
            QLabel:active {
            background-color: transparent;  /* Ensure QLabel changes with selection */
            }
            """
        )
        # Discover existing cache data
        self.discover_existing_cache()  # This will run in a separate thread because its a long process

    def reload_list(self):
        try:
            self.file_list.clear()
            worlds = self.record_manager.read_record("Worlds")
            if worlds:
                for world in worlds:
                    thumbnail_path = world.get(
                        "Thumbnail Path", "./resources/default_thumbnail.png"
                    )
                    world_name = world.get("World Name", "Unknown")
                    world_author = world.get("World Author", "Unknown")

                    list_item_widget = ListItemWidget(
                        thumbnail_path, world_name, world_author, world["World ID"]
                    )
                    list_item = QListWidgetItem(self.file_list)
                    list_item.setSizeHint(list_item_widget.sizeHint())

                    list_item.world_id = world["World ID"]

                    # Add the item and set the widget within the loop
                    self.file_list.addItem(list_item)
                    self.file_list.setItemWidget(list_item, list_item_widget)
        except Exception as e:
            self.handle_error(str(e))
            raise

    def rename_file(self, record_manager):
        try:
            selected_item = self.file_list.currentItem()
            if selected_item:
                new_name, ok = QInputDialog.getText(
                    self,
                    "Rename World",
                    "Enter new world name:",
                    text=selected_item.text(),
                )
                if ok:
                    record_manager.rename_record(selected_item.world_id, new_name)
                    self.reload_list()
        except Exception as e:
            self.handle_error(str(e))
            raise

    def delete_file(self):
        try:
            selected_item = self.file_list.currentItem()
            if selected_item:
                reply = QMessageBox.question(
                    self,
                    "Delete file",
                    "Are you sure you want to delete this file?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # PURGE IT
                    self.record_manager.remove_record(selected_item.world_id)
                    asset_bundle_path = f"./assetbundles/{selected_item.world_id}"
                    thumbnail_path = (
                        f"./assetbundles/thumbnails/{selected_item.world_id}.png"
                    )
                    if os.path.exists(asset_bundle_path):
                        os.remove(asset_bundle_path)  # Remove the asset bundle
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)  # Remove the thumbnail
                    self.reload_list()
        except Exception as e:
            self.handle_error(str(e))
            raise

    def view_file_info(self):
        try:
            selected_item = self.file_list.currentItem()
            if not selected_item:
                # No item selected, do nothing
                return
            selected_world_id = selected_item.world_id
            if selected_world_id:

                information = self.record_manager.read_record("Worlds")

                world_info = next(
                    (
                        world
                        for world in information
                        if world["World ID"] == selected_world_id
                    ),
                    None,
                )
                if world_info:
                    worldname = world_info.get("World Name", "Unknown")
                    worldauthor = world_info.get("World Author", "Unknown")
                    worlddescription = world_info.get(
                        "World Description", "No description available."
                    )
                    worldid = world_info.get(
                        "World ID", "Unknown ID"
                    )  # If this returns "Unknown ID", something went really wrong
                else:
                    self.handle_error("World information not found.")
                    return

                formatted_info = (
                    f"<b>Name:</b> {worldname}<br>"
                    f"<hr>"
                    f"<b>Author:</b> {worldauthor}<br>"
                    f"<hr>"
                    f"<b>Description:</b> {worlddescription}<br>"
                    f"<hr>"
                    f"<b>ID:</b> {worldid}"
                )

                if selected_item:
                    QMessageBox.information(
                        self, "World Information", f"{formatted_info}"
                    )
            else:
                self.handle_error(
                    "This selection has no ID associated with it. This shouldn't happen."
                )
        except Exception as e:
            self.handle_error(str(e))

    def replace_errorworld(self):
        try:
            if not self.vrchat_cache_path.text():
                QMessageBox.warning(
                    self,
                    "Error",
                    "Please specify the path to the VRChat cache directory.",
                )
                print("Error: VRChat cache directory path not specified.")
            else:
                try:
                    target_path = os.path.join(
                        self.vrchat_exec_path.text(),
                        "VRChat_Data",
                        "StreamingAssets",
                        "Worlds",
                    )
                    errorworld_path = os.path.join(target_path, "errorworld.vrcw")
                    print(f"Target path for errorworld.vrcw: {errorworld_path}")

                    if os.path.exists(errorworld_path):
                        os.remove(errorworld_path)
                        print(f"Removed existing errorworld.vrcw at {errorworld_path}")

                    selected_world_id = self.file_list.currentItem().world_id
                    source_path = f"./assetbundles/{selected_world_id}"
                    shutil.copyfile(source_path, errorworld_path)
                    print(f"Copied {source_path} to {errorworld_path}")
                    print("Replaced errorworld.vrcw with the selected world.")
                except Exception as e:
                    self.handle_error(str(e))
                    print(
                        f"Exception occurred while replacing errorworld.vrcw: {str(e)}"
                    )
                    raise
        except Exception as e:
            self.handle_error(str(e))
            print(f"Exception occurred: {str(e)}")
            raise

    def browse_file(self, line_edit):
        try:
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
        except Exception as e:
            self.handle_error(str(e))
            raise

    def prompt_for_world_url(self, assetbundle_path): # To be deprecated, we can extract the world ID from the assetbundle
        try:
            self.activateWindow()  # Focus the window
            while True:
                url, ok = QInputDialog.getText(
                    self,
                    "Enter World URL",
                    "Enter the URL for the newly downloaded world:",
                )
                if ok:
                    if self.is_valid_vrchat_url(url):
                        self.process_world_url(assetbundle_path, url)
                        break
                    else:
                        self.handle_error(
                            "Invalid VRChat URL. Please enter a valid URL."
                        )
                else:
                    break
        except Exception as e:
            self.handle_error(str(e))
            raise

    def search_hex_data_for_world_id(self, assetbundle_path):
        try:
            with open(assetbundle_path, "rb") as f:
                data = f.read()
                utf8_data = data.decode(
                    "utf-8", "ignore"
                )  # Decode as UTF-8, ignore non UTF-8 compatible chars
                world_id_start_str = "wrld_"
                world_id = None
                start_index = utf8_data.find(world_id_start_str)

                if start_index != -1:
                    start_index += len(world_id_start_str)  # start after "wrld_"
                    end_index = start_index
                    while end_index < len(utf8_data):
                        char = utf8_data[end_index]
                        # Detect if we hit a character that's not part of the world_id
                        if not char.isalnum() and char != "-":
                            break
                        end_index += 1
                    # 🎉 Found world ID 🎉
                    world_id = world_id_start_str + utf8_data[start_index:end_index]

                return world_id
        except Exception as e:
            self.handle_error(str(e))
            return None

    def is_valid_vrchat_url(self, url):
        return url.startswith("https://vrchat.com/") and "wrld_" in url

    def url_to_id(self, url):
        try:
            print(url)  # debug, will remove later
            if "wrld_" in url:
                return "wrld_" + url.split("wrld_")[1]
            else:
                self.handle_error("Invalid URL format.")
                return None
        except Exception as e:
            self.handle_error(str(e))
            return None

    def process_world_url(self, assetbundle_path, url):
        try:
            if url:
                try:
                    world_info = get_world_info(self.url_to_id(url))
                    if not world_info:
                        world_info = self.manual_input_world_info()

                    self.record_manager.add_record("Worlds", world_info)
                    self.copy_asset_bundle(assetbundle_path, world_info)

                    thumbnail_path = world_info.get(
                        "Thumbnail Path", "./resources/default_thumbnail.png"
                    )
                    world_name = world_info.get("World Name", "Unknown")
                    world_author = world_info.get("World Author", "Unknown")

                    world_id = world_info.get("World ID", "Unknown ID")
                    list_item_widget = ListItemWidget(
                        thumbnail_path, world_name, world_author, world_id
                    )
                    list_item = QListWidgetItem(self.file_list)
                    list_item.setSizeHint(list_item_widget.sizeHint())

                    # Add the world id
                    list_item.world_id = world_info["World ID"]

                    # Add the item and set the widget within the loop
                    self.file_list.addItem(list_item)
                    self.file_list.setItemWidget(list_item, list_item_widget)
                except Exception as e:
                    # we want a stack trace for debugging
                    raise e
            else:
                self.handle_error("No URL provided.")
        except Exception as e:
            self.handle_error(str(e))
            raise

    def manual_input_world_info(self):
        try:
            world_name, ok = QInputDialog.getText(
                self, "Manual Input", "Enter World Name:"
            )
            if not ok:
                return None

            world_author, ok = QInputDialog.getText(
                self, "Manual Input", "Enter World Author:"
            )
            if not ok:
                return None

            while True:
                world_id, ok = QInputDialog.getText(
                    self, "Manual Input", "Enter World ID:"
                )
                if not ok:
                    return None
                if world_id.strip():
                    break
                else:
                    QMessageBox.warning(
                        self, "Invalid Input", "World ID cannot be blank."
                    )

            return {
                "World Name": world_name,
                "World Author": world_author,
                "World ID": world_id,
                "Thumbnail Path": "./resources/default_thumbnail.png",
            }
        except Exception as e:
            self.handle_error(str(e))
            return None

    def copy_asset_bundle(self,assetbundle_path, world_info):
        try:
            asset_bundle_manager = AssetBundleManager()
            asset_bundle_manager.copy_asset_bundle(assetbundle_path, "./assetbundles", world_info["World ID"])
        except Exception as e:
            self.handle_error(str(e))
            raise

    def handle_error(self, message):
        raise Exception(message)
        

    def launch_vrchat(self):
        try:
            if not self.vrchat_exec_path.text():
                QMessageBox.warning(
                    self, "Error", "Please specify the path to the VRChat executable."
                )
            else:

                def launch_vrchat_thread():
                    os.system(f'"{self.vrchat_exec_path.text()}/vrchat.exe"')

                threading.Thread(target=launch_vrchat_thread).start()
                print("Launching VRChat...")
        except Exception as e:
            self.handle_error(str(e))
            raise

    def discover_existing_cache(self):
        if not self.vrchat_cache_path.text():
            return None  # No cache path specified, probably a first launch

        def worker():
            try:
                # Get all "__data" files
                data_files = []
                for root, _, files in os.walk(self.vrchat_cache_path.text()):
                    for file in files:
                        if file == "__data":
                            data_files.append(os.path.join(root, file))
                print(f"Discovered {len(data_files)} '__data' files.")

                new_worlds = []  # To store newly discovered worlds
                for data_file in data_files:
                    world_id = self.search_hex_data_for_world_id(data_file)
                    if world_id and not self.record_manager.record_exists(world_id):
                        print(f"Discovered new world ID: {world_id}")
                        world_info = get_world_info(world_id)
                        if not world_info:
                            continue
                        self.record_manager.add_record("Worlds", world_info)
                        self.copy_asset_bundle(data_file, world_info)

                        # Append new world info to the list
                        new_worlds.append(world_info)

                # Now enqueue update to the main UI thread
                if new_worlds:
                    QMetaObject.invokeMethod(self, "add_worlds_to_list", Qt.ConnectionType.QueuedConnection, Q_ARG(list, new_worlds))
                    print("Added new worlds to the list.")
            except Exception as e:
                raise e # we want a stack trace for debugging

        threading.Thread(target=worker).start()

    @pyqtSlot(list)
    def add_worlds_to_list(self, new_worlds):
        try:
            for world_info in new_worlds:
                thumbnail_path = world_info.get("Thumbnail Path", "./resources/default_thumbnail.png")
                world_name = world_info.get("World Name", "Unknown")
                world_author = world_info.get("World Author", "Unknown")
                world_id = world_info.get("World ID", "Unknown ID")

                list_item_widget = ListItemWidget(thumbnail_path, world_name, world_author, world_id)
                list_item = QListWidgetItem(self.file_list)
                list_item.setSizeHint(list_item_widget.sizeHint())

                list_item.world_id = world_id

                # Add the item and set the widget
                self.file_list.addItem(list_item)
                self.file_list.setItemWidget(list_item, list_item_widget)
        except Exception as e:
            # we want a stack trace for debugging
            raise e

    def closeEvent(self, event):
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            event.accept()
        except Exception as e:
            self.handle_error(str(e))
            raise


# if __name__ == "__main__":
#     # Debugging only
#     qapplication = QApplication(sys.argv)
#     qt_gui_manager = QtGUIManager()
#     assetbundle_test_path = 'C:\\Users\\Neon\\Documents\\GitHub\\VRCacheManager\\assetbundles\\__data'
#     print(qt_gui_manager.search_hex_data_for_world_id(assetbundle_test_path))
