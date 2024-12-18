# VRCacheManager

VRCacheManager is a tool designed to manage VRChat cache files, allowing you to rename, delete, view information, and replace the ErrorWorld. 

This project is intended for those who would like to view VRChat worlds without running Easy Anti-Cheat (EAC) or for those who would like to preserve their favorite worlds.

## Features

- **Rename Files**: Rename cache files for better organization.
- **Delete Files**: Delete unwanted cache files.
- **View File Information**: View detailed information about cache files.
- **Replace Error Worlds**: Replace error worlds with valid ones.
- **Monitor Cache Directory**: Automatically detect new files in the VRChat cache directory.
- **Launch VRChat**: Launch VRChat directly from the application.
- **Web Scrape World Data**: Fetch world data from the web.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ItsAlphaNeon/VRCacheManager.git
    ```
2. Navigate to the project directory:
    ```sh
    cd VRCacheManager
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the application:
    ```sh
    python main.py
    ```
2. Use the UI to manage your VRChat cache files.

## Dependencies

- Python 3.10+
- PyQt6
- watchdog
- requests
- BeautifulSoup4

## File Structure

- `main.py`: Entry point of the application.
- `archive_manager.py`: Contains the main UI and logic for managing cache files.
- `recordmanager.py`: Handles reading and writing records to a JSON file.
- `cache_event_handler.py`: Monitors the cache directory for new files.
- `asset_bundle_manager.py`: Manages asset bundle files.
- `worlddata.py`: Fetches world data from the web.
- `README.md`: Project documentation.

## Contributing

Contributions are not currently accepted for this project. Sorry!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [PyQt](https://riverbankcomputing.com/software/pyqt/intro) for the UI framework.
- [watchdog](https://github.com/gorakhargosh/watchdog) for file system event monitoring.
