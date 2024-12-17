import sys
from PyQt6.QtWidgets import (
    QApplication,
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
)

class ArchiveManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("VRChat Cache Archive Manager")
        self.setGeometry(100, 100, 600, 400)

        # Main Layout
        main_layout = QHBoxLayout()

        # File list section
        self.file_list = QListWidget()
        self.file_list.addItems(["file1", "file2", "file3"])  # Dummy entries

        # Control Panel Layout
        control_layout = QVBoxLayout()

        # Buttons
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.view_btn = QPushButton("View Metadata")

        # Button actions
        self.rename_btn.clicked.connect(self.renameFile)
        self.delete_btn.clicked.connect(self.deleteFile)
        self.view_btn.clicked.connect(self.viewFileMetadata)

        # Loading VRChat Paths
        # TODO: keep this in a config file
        # TODO: vrchat exec should be a file, not a directory
        self.vrchat_exec_path = QLineEdit()
        self.vrchat_exec_browse = QPushButton("Browse...")
        self.vrchat_exec_browse.clicked.connect(
            lambda: self.browseFile(self.vrchat_exec_path)
        )

        self.vrchat_cache_path = QLineEdit()
        self.vrchat_cache_browse = QPushButton("Browse...")
        self.vrchat_cache_browse.clicked.connect(
            lambda: self.browseFile(self.vrchat_cache_path)
        )

        self.launch_vrchat_btn = QPushButton("Launch VRChat")
        self.launch_vrchat_btn.clicked.connect(self.launchVRChat)

        # Adding controls to control panel
        control_layout.addWidget(QLabel("Controls:"))
        control_layout.addWidget(self.rename_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.view_btn)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("VRChat Executable:"))
        control_layout.addWidget(self.vrchat_exec_path)
        control_layout.addWidget(self.vrchat_exec_browse)
        control_layout.addWidget(QLabel("VRChat Cache Directory:"))
        control_layout.addWidget(self.vrchat_cache_path)
        control_layout.addWidget(self.vrchat_cache_browse)
        control_layout.addWidget(self.launch_vrchat_btn)

        # Setup main layout
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

    def renameFile(self):
        selected_item = self.file_list.currentItem()
        if selected_item:
            new_name, ok = QInputDialog.getText(
                self, "Rename file", "Enter new name:", text=selected_item.text()
            )
            if ok:
                selected_item.setText(new_name)

    def deleteFile(self):
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
                self.file_list.takeItem(self.file_list.row(selected_item))

    def viewFileMetadata(self):
        selected_item = self.file_list.currentItem()
        if selected_item:
            QMessageBox.information(
                self, "File Metadata", f"Display metadata for {selected_item.text()}"
            )

    def browseFile(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)

    def launchVRChat(self):
        if not self.vrchat_exec_path.text():
            QMessageBox.warning(
                self, "Error", "Please specify the path to the VRChat executable."
            )
        else:
            # VRC launching would be here
            QMessageBox.information(self, "Launch VRChat", "Launching VRChat...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ArchiveManager()
    ex.show()
    sys.exit(app.exec())
