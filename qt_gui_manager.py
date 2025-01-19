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
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QIcon, QPixmap
# from cache_event_handler import CacheEventHandler
from asset_bundle_manager import AssetBundleManager
import record_manager as RecordManager
from vrchat_api_manager import VRChatAPIManager
# from worlddata import get_world_info # Deprecated, this script sucked ass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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


class StatusUpdater(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

# This handles cache events, moved from the legacy script
class CacheEventHandler(FileSystemEventHandler, QObject):
    new_file_detected = pyqtSignal(str, bool)  # Signal to emit new file path and a boolean
    
    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def on_created(self, event):
        if event.is_directory:
            return
        if "__data" in event.src_path:
            # Emit the signal with the path of the new `__data` file
            self.new_file_detected.emit(event.src_path, True)
            print(f"Detected new file: {event.src_path}")


class QtGUIManager(QWidget):
    # Variables - Informative
    total_worlds = 0
    new_worlds = 0
    unknown_worlds = 0
    
    # Signal for updating status label
    update_status_label_signal = pyqtSignal(str)
    add_worlds_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.api_manager = VRChatAPIManager()
        self.api_manager.username_password_signal.connect(self.show_username_password_prompt)
        self.api_manager.two_factor_signal.connect(self.show_two_factor_prompt)
        self.update_status_label_signal.connect(self.update_status_label)
        self.add_worlds_signal.connect(self.add_worlds_to_list)
        
        # Authenticate the header for the API
        self.api_manager.authenticate(None, None, "vrc@freevrc.com") # This email is for VRChat to contact us. This may change in the future.

        # Initialize the observer
        self.observer = None

        # Initialize the UI
        self.init_ui()

    def show_username_password_prompt(self):
        username, ok1 = QInputDialog.getText(self, "Login", "Enter Username:")
        if not ok1:
            return
        password, ok2 = QInputDialog.getText(self, "Login", "Enter Password:", QLineEdit.EchoMode.Password)
        if not ok2:
            return
        api_usage_email, ok3 = QInputDialog.getText(self, "Login", "Enter API Usage Email:")
        if not ok3:
            return
        self.api_manager.authenticate(username, password, api_usage_email)

    def show_two_factor_prompt(self, message):
        code, ok = QInputDialog.getText(self, "Two-Factor Authentication", message)
        if ok:
            self.api_manager.verify_two_factor_code(code)

    def start_watching(self, path):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # Instantiate the event handler
        event_handler = CacheEventHandler()

        # Connect the signal to the appropriate slot in your GUI
        event_handler.new_file_detected.connect(self.process_new_world_path)

        # Initialize and start the observer
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        print(f"Watching {path} for changes...")


    def init_ui(self):
        self.setWindowTitle("VRCacheManager")
        self.setGeometry(100, 100, 800, 400)

        # Main layout for the worlds list
        main_layout = QVBoxLayout()
        self.record_manager = RecordManager.RecordManager(
            "records.json", "./assetbundles"
        )
        self.record_manager.verify_integrity("assetbundles")

        # Info label
        self.info_label = QLabel("0 worlds found, 0 new, 0 unknown") # Placeholder text
        
        # Status Label
        self.status_label = QLabel("Status: Idle")

        # World list widget
        self.file_list = QListWidget()

        # Load the list of worlds
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
        # End of loading the list of worlds

        # Add status label and file list to the main layout
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.file_list)

        # Control layout for the buttons
        control_layout = QVBoxLayout()
        
        # Create a layout for split "reload / discover" button
        reload_discover_layout = QHBoxLayout()
        
        # Add a reload button to the discover button
        self.reload_btn = QPushButton("Reload List")
        self.reload_btn.setToolTip("Reload the list of worlds")
        self.reload_btn.setIcon(QIcon("./resources/reload_icon.svg"))
        self.reload_btn.clicked.connect(self.reload_list)
        reload_discover_layout.addWidget(self.reload_btn)
        
        # Add a discover button to the layout
        self.discover_btn = QPushButton("Discover Worlds")
        self.discover_btn.setToolTip("Discover worlds in the VRChat cache. (This is experimental, and will not work 100% of the time.)")
        self.discover_btn.setIcon(QIcon("./resources/discover_icon.svg"))
        self.discover_btn.clicked.connect(self.discover_existing_cache)
        reload_discover_layout.addWidget(self.discover_btn)
        
        # Add the reload/discover layout to the main layout
        main_layout.addLayout(reload_discover_layout)

        # Add status label and file list to the main layout
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.view_btn = QPushButton("View Info")
        self.replace_errorworld_btn = QPushButton("Replace ErrorWorld")
        self.open_in_explorer_btn = QPushButton("Open in Explorer")

        self.rename_btn.setToolTip("Rename the selected world")
        self.delete_btn.setToolTip("Delete the selected world")
        self.view_btn.setToolTip("View information about the selected world")
        self.replace_errorworld_btn.setToolTip(
            "Replace the error world with the selected world"
        )
        self.open_in_explorer_btn.setToolTip("Open the selected world in your file explorer")

        # Connect the buttons to their respective functions
        self.rename_btn.clicked.connect(lambda: self.rename_file())
        self.delete_btn.clicked.connect(self.delete_file)
        self.view_btn.clicked.connect(self.view_file_info)
        self.replace_errorworld_btn.clicked.connect(self.replace_errorworld)
        self.open_in_explorer_btn.clicked.connect(self.open_in_explorer)

        # VRChat executable path
        self.vrchat_exec_path = QLineEdit()
        self.vrchat_exec_browse = QPushButton("Browse...")
        self.vrchat_exec_browse.setToolTip("Browse for the VRChat executable")
        self.vrchat_exec_browse.clicked.connect(
            lambda: self.browse_executable(self.vrchat_exec_path)
        )
        # VRChat cache directory
        self.vrchat_cache_path = QLineEdit()
        self.vrchat_cache_browse = QPushButton("Browse...")
        self.vrchat_cache_browse.setToolTip("Browse for the VRChat cache directory")
        self.vrchat_cache_browse.clicked.connect(
            lambda: self.browse_file(self.vrchat_cache_path)
        )
        
        # Login to VRChat API Button
        self.login_vrchat_btn = QPushButton("Login to VRChat API")
        self.login_vrchat_btn.setToolTip("Login to VRChat API")
        self.login_vrchat_btn.clicked.connect(self.show_username_password_prompt)
        # TODO: Finish implementing a full login, but for now we'll disable the button
        # Simple world API calls don't require authentication
        self.login_vrchat_btn.setEnabled(False)
        self.login_vrchat_btn.setToolTip("This isn't needed quite yet, we're just future-proofing")

        # Launch VRChat button
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
        self.login_vrchat_btn.setIcon(QIcon("./resources/login_icon.svg"))
        self.open_in_explorer_btn.setIcon(QIcon("./resources/open_icon.svg"))

        # Load the paths from the records
        if self.record_manager.verify_record("vrchat_exec"):
            self.vrchat_exec_path.setText(
                self.record_manager.read_record("vrchat_exec")
            )
        if self.record_manager.verify_record("vrchat_cache"):
            self.vrchat_cache_path.setText(
                self.record_manager.read_record("vrchat_cache")
            )
            self.start_watching(self.vrchat_cache_path.text())

        # Add the controls to the layout
        control_layout.addWidget(QLabel("Controls:"))
        control_layout.addWidget(self.rename_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.view_btn)
        control_layout.addWidget(self.replace_errorworld_btn)
        control_layout.addWidget(self.open_in_explorer_btn)
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

        # This isn't needed yet, I'm just future proofing
        # control_layout.addWidget(self.login_vrchat_btn)
        control_layout.addWidget(self.launch_vrchat_btn)

        # Create a horizontal layout to contain both main and controls with size stretches
        container_layout = QHBoxLayout()
        container_layout.addLayout(main_layout, 3)  # main_layout will take 3 parts
        container_layout.addLayout(control_layout, 1)  # control_layout will take 1 part

        self.setLayout(container_layout)

        self.reload_list() 
        
        # Stylesheet
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
            background-color: transparent; 
            color: #CCCCCC;
            }
            QListWidget::item:selected {
            background-color: #505052;
            color: #FFFFFF;
            }
            QLabel {
            font-weight: bold;
            background-color: transparent;
            }
            QLabel:active {
            background-color: transparent;
            }
            """
        )
        
    def update_info_label(self, total_worlds, new_worlds, unknown_worlds):
        self.info_label.setText(f"{total_worlds} worlds found, {new_worlds} new, {unknown_worlds} unknown")
        
    def update_status_label(self, status):
        self.status_label.setText(f"Status: {status}")

    def reload_list(self):  # clears and re-populates the list
        self.update_status_label("Reloading list...")
        try:
            self.file_list.clear()
            worlds = self.record_manager.read_record("Worlds")
            if worlds:
                world_count = 0
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
                    world_count += 1
                # Update the total worlds count
                self.total_worlds = world_count
            # Update the status label        
            self.update_info_label(self.total_worlds, self.new_worlds, self.unknown_worlds)
            self.update_status_label("Idle")
        except Exception as e:
            self.handle_error(str(e))
            raise

    def rename_file(
        self,
    ):  # Renames the selected world (Not the file itself, just the name in the records)
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
                    record = next((world for world in self.record_manager.read_record("Worlds") if world["World ID"] == selected_item.world_id), None)
                    if record is None:
                        self.handle_error("World ID not found in records.")
                        return
                    old_name = record["World Name"]
                    target_dir = os.path.join("./assetbundles", old_name)

                    
                    # Rename the directory
                    new_target_dir = os.path.join("./assetbundles", new_name)
                    os.rename(target_dir, new_target_dir)
                    # Update the record
                    self.record_manager.rename_record(selected_item.world_id, new_name)
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
                    worlds = self.record_manager.read_record("Worlds") # Save this as a var since we're deleting it
                    
                    
                    print(worlds) # debug
                    
                    # Delete the directory
                    dir_name = next((world for world in worlds if world["World ID"] == selected_item.world_id), None)
                    if dir_name is None:
                        self.handle_error("World ID not found in records.")
                        return
                    target_dir = os.path.join("./assetbundles", dir_name["World Name"])
                    
                    shutil.rmtree(target_dir)

                    # Remove the thumbnail
                    thumbnail_path = next((world for world in worlds if world["World ID"] == selected_item.world_id), None)
                    if thumbnail_path is None:
                        self.handle_error("World ID not found in records.")
                        return
                    thumbnail_path = os.path.join("./assetbundles/thumbnails", os.path.basename(dir_name["Thumbnail Path"]))
                    os.remove(thumbnail_path)
                    
                    # Remove the record
                    self.record_manager.remove_record(selected_item.world_id)
                    
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

    def replace_errorworld(self):  # Replaces the errorworld.vrcw with the selected world
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
                        os.path.dirname(self.vrchat_exec_path.text()),
                        "VRChat_Data",
                        "StreamingAssets",
                        "Worlds",
                    )
                    errorworld_path = os.path.join(target_path, "errorworld.vrcw")
                    print(f"Target path for errorworld.vrcw: {errorworld_path}")

                    if os.path.exists(errorworld_path):
                        os.remove(errorworld_path)
                        print(f"Removed existing errorworld.vrcw at {errorworld_path}")

                    selected_item = self.file_list.currentItem()
                    if selected_item:
                        selected_world_id = selected_item.world_id
                        world_info = self.record_manager.read_record("Worlds")
                        world_name = next(
                            (world["World Name"] for world in world_info if world["World ID"] == selected_world_id),
                            None
                        )
                        if world_name:
                            source_path = os.path.join("./assetbundles", world_name, selected_world_id)
                            shutil.copyfile(source_path, errorworld_path)
                            print(f"Copied {source_path} to {errorworld_path}")
                            print("Replaced errorworld.vrcw with the selected world.")
                        else:
                            self.handle_error("World name not found.")
                    else:
                        self.handle_error("No world selected.")
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

    def browse_file(self, line_edit):  # Opens a file dialog to browse for a file
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
    
    def browse_executable(self, line_edit):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select VRChat Executable",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        if file_name:
            line_edit.setText(file_name)
            self.record_manager.remove_record("vrchat_exec")
            self.record_manager.add_record("vrchat_exec", file_name)
            print("Saved VRChat executable path.")
            
    import os

    def open_in_explorer(self):
        try:
            selected_item = self.file_list.currentItem()
            if not selected_item:
                return  # Do nothing if no item is selected
            selected_world_id = selected_item.world_id
            if selected_world_id:
                world_info = self.record_manager.read_record("Worlds")
                world_name = next(
                    (world["World Name"] for world in world_info if world["World ID"] == selected_world_id),
                    None
                )
                if world_name:
                    asset_bundle_path = os.path.abspath(f"./assetbundles/{world_name}/{selected_world_id}")
                    if os.path.exists(asset_bundle_path):
                        if os.name == 'nt':  # Windows
                            os.system(f'explorer /select,"{asset_bundle_path}"')
                        elif os.name == 'posix':  # Linux
                            os.system(f'xdg-open "{asset_bundle_path}"')
                        else:
                            self.handle_error("Unsupported operating system.")
                    else:
                        self.handle_error("Asset bundle not found.")
                else:
                    self.handle_error("World name not found.")
            else:
                self.handle_error("World ID not found.")
        except Exception as e:
            self.handle_error(str(e))


    def search_hex_data_for_world_id(
        self, assetbundle_path
    ):  # Searches the assetbundle for the world ID in hex data
        try:
            with open(assetbundle_path, "rb") as f:
                data = f.read()
                utf8_data = data.decode(
                    "utf-8", "ignore"
                )  # Decode as UTF-8, ignore non UTF-8 compatible chars
                world_id_start_str = "wrld_"
                world_ids = []
                start_index = utf8_data.find(world_id_start_str)

                while start_index != -1 and len(world_ids) < 10:
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
                    world_ids.append(world_id)
                    # Look for the next occurrence
                    start_index = utf8_data.find(world_id_start_str, end_index)

                if world_ids:
                    # Return the longest world ID found
                    return max(world_ids, key=len)
                return None
        except Exception as e:
            self.handle_error(str(e))
            return None

    def prompt_for_world_url(self):
        while True:
            url, ok = QInputDialog.getText(self, "Manual World URL", "Something went wrong while automatically detecting the world ID. Please enter the world URL or ID:")
            if not ok:
                print("User cancelled the input dialog.")
                return None
            extracted_id = None
            print(f"User entered: {url}")
            if "vrchat.com/home/world/" in url:
                print("Detected URL format: vrchat.com/home/world/")
                extracted_id = url.split("vrchat.com/home/world/")[1].split("/")[0]
                print(f"Extracted ID from URL: {extracted_id}")
            elif str(url).startswith("wrld_"):
                print("Detected ID format: wrld_")
                extracted_id = url.split("/")[0]  # Remove any trailing parts like /info
                print(f"Extracted ID: {extracted_id}")
            else:
                print("Invalid input format. Neither a valid URL nor an ID.")
            if extracted_id:
                print(f"Returning extracted ID: {extracted_id}")
                return extracted_id
            QMessageBox.warning(self, "Invalid Input", "The input provided is not a valid VRChat world URL or ID. Please try again.")

    def copy_asset_bundle(self, assetbundle_path, world_info):  # Copies the asset bundle to a folder named after the world
        try:
            asset_bundle_manager = AssetBundleManager()
            world_name = world_info["World Name"]
            destination_dir = os.path.join("./assetbundles", world_name)
            os.makedirs(destination_dir, exist_ok=True)
            asset_bundle_manager.copy_asset_bundle(
                assetbundle_path, destination_dir, world_info["World ID"]
            )
        except Exception as e:
            self.handle_error(str(e))
            raise

    def handle_error(self, message):
        # Display the error message to the user
        # QMessageBox.critical(self, "Error", message)
        # Log the error message if needed
        print(f"Error: {message}")

    def launch_vrchat(self):  # Launches VRChat. Crazy.
        try:
            if not self.vrchat_exec_path.text():
                QMessageBox.warning(
                    self, "Error", "Please specify the path to the VRChat executable."
                )
            else:

                def launch_vrchat_thread():
                    os.system(f'"{self.vrchat_exec_path.text()}"')

                threading.Thread(target=launch_vrchat_thread).start()
                print("Launching VRChat...")
        except Exception as e:
            self.handle_error(str(e))
            print(f"Exception occurred: {str(e)}")
            raise

    def discover_existing_cache(self): # This should only be called once at the start of the program
        
        self.unknown_worlds = 0 # Reset the unknown worlds count
        self.update_status_label("Discovering existing cache data...")

        def worker():
            try:
                data_files = []
                for root, _, files in os.walk(self.vrchat_cache_path.text()):
                    for file in files:
                        if file == "__data":
                            data_files.append(os.path.join(root, file))
                print(f"Discovered {len(data_files)} '__data' files.")

                new_worlds = []
                for data_file in data_files:
                    world_id = self.search_hex_data_for_world_id(data_file)
                    if world_id and not self.record_manager.record_exists(world_id):
                        print(f"Discovered new world ID: {world_id}")
                        world_JSON = self.api_manager.get_world_from_id(world_id)
                        world_info = self.api_manager.get_legacy_format_world_info(world_JSON)
                        if not world_info:
                            self.unknown_worlds += 1
                            continue

                        self.store_world_info(self.record_manager, world_info)
                        self.copy_asset_bundle(data_file, world_info)

                        new_worlds.append(world_info)

                self.add_worlds_signal.emit(new_worlds)
                self.update_status_label_signal.emit("Idle")
                
                self.add_worlds_signal.emit(new_worlds)
            except Exception as e:
                self.handle_error(str(e))
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
                list_item = QListWidgetItem()
                list_item.setSizeHint(list_item_widget.sizeHint())

                list_item.world_id = world_id

                self.file_list.addItem(list_item)
                self.file_list.setItemWidget(list_item, list_item_widget)
        except Exception as e:
            self.handle_error(str(e))

    def closeEvent(self, event):  # Closes the application
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            event.accept()
        except Exception as e:
            self.handle_error(str(e))
            raise
    
    # These two functions should be used together to store world info in the records
    def store_world_info(self, record_manager, world_info): # Stores world info in the records
        try:
            record_manager.add_record("Worlds", world_info)
        except Exception as e:
            self.handle_error(str(e))
            raise
    def copy_asset_bundle(self, assetbundle_path, world_info): # Copies the asset bundle to the assetbundles directory
        try:
            asset_bundle_manager = AssetBundleManager()
            world_name = world_info["World Name"]
            destination_dir = os.path.join("./assetbundles", world_name)
            os.makedirs(destination_dir, exist_ok=True)
            asset_bundle_manager.copy_asset_bundle(
                assetbundle_path, destination_dir, world_info["World ID"]
            )
        except Exception as e:
            self.handle_error(str(e))
            raise
    
    def process_new_world_path(self, path, newly_downloaded=False):
        # path is the path to the assetbundle in the VRChat Cache
        # This is the main function to processing and storing records. All other functions should be called from here
        
        world_id = None # ID of the VRCW (wrld_...)
        world_JSON = None # JSON data from the VRChat API
        world_info = None # This is our own format for storing world info
        
        # Get the world ID from the assetbundle
        world_id = self.search_hex_data_for_world_id(path)
        if len(str(world_id)) < 35:
            print(f"World ID: {world_id}")
            print("Seemingly invalid world ID, skipping...")
            return
        
        # Get the world JSON from the VRChat API
        world_JSON = self.api_manager.get_world_from_id(world_id)
        if not world_JSON:
            if newly_downloaded:
                print("Failed to get world JSON, likely invalid. Prompting for world URL...")
                world_id = self.prompt_for_world_url()
                if not world_id:
                    print("User cancelled, skipping...")
                    return
                world_JSON = self.api_manager.get_world_from_id(world_id)
                if not world_JSON:
                    print("This world is fucked. Sorry. There should be no way to get here.")
                    return
        
        # Get the world info in our own format
        world_info = self.api_manager.get_legacy_format_world_info(world_JSON)
        if not world_info:
            print("Failed to get world info, skipping...")
            return
        
        # Check if the world ID is already stored in the record manager
        if self.record_manager.record_exists(world_id):
            print(f"World ID {world_id} already exists in the records, skipping...")
            return

        # Store the world info in the records (uses world_info)
        self.store_world_info(self.record_manager, world_info)
        
        # Copy the assetbundle to the assetbundles directory (uses assetbundle_path and world_info)
        self.copy_asset_bundle(path, world_info)
        
        print("If you see this message, the world has been processed successfully.")
        
        self.reload_list()


# if __name__ == "__main__":
    # Debugging only
    # qapplication = QApplication(sys.argv)
    # qt_gui_manager = QtGUIManager()
    # assetbundle_test_path = (
    #     "C:\\Users\\Neon\\Documents\\GitHub\\VRCacheManager\\assetbundles\\__data"
    # )
    # qt_gui_manager.show()
    # sys.exit(qapplication.exec())
