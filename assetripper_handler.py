import requests
import zipfile
import os

class AssetRipperHandler:
    
    def __init__(self):
        self.platform_asset_name = None
    def get_platform_asset_name(self):
        if os.name == 'nt':
            self.platform_asset_name = 'AssetRipper_win_x64.zip'
        elif os.name == 'posix':
            self.platform_asset_name = 'AssetRipper_linux_x64.zip'
        else:
            print("Unsupported platform.")
            self.platform_asset_name = None  
        return self.platform_asset_name

    def download_latest(self, install_dir):
        self.get_platform_asset_name()
        
        if not self.platform_asset_name:
            print("Platform asset name is not set. Exiting.")
            return
        
        api_url = "https://api.github.com/repos/AssetRipper/AssetRipper/releases/latest"
        print(f"Fetching latest release information from {api_url}")
        response = requests.get(api_url)
        if response.status_code == 200:
            latest_release = response.json()
            download_url = None
            for asset in latest_release['assets']:
                if asset['name'] == self.platform_asset_name:
                    download_url = asset['browser_download_url']
                    break
            if download_url:
                print(f"Downloading {self.platform_asset_name} from {download_url}")
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    file_path = os.path.join(install_dir, self.platform_asset_name)
                    with open(file_path, 'wb') as file:
                        file.write(download_response.content)
                    print(f"Downloaded {self.platform_asset_name} to {file_path}")
                else:
                    print(f"Failed to download AssetRipper. Status code: {download_response.status_code}")
            else:
                print(f"{self.platform_asset_name} not found in the latest release.")
        else:
            print(f"Failed to fetch the latest release information. Status code: {response.status_code}")
        return
    
    def extract_zip(self, zip_path, extract_path):
        print(f"Extracting {zip_path} to {extract_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print(f"Extraction complete.")
        return
    
    def uninstall_asset_ripper(self, install_dir):
        asset_ripper_dir = os.path.join(install_dir, self.platform_asset_name)
        if os.path.exists(asset_ripper_dir):
            print(f"Uninstalling AssetRipper from {asset_ripper_dir}")
            os.rmdir(asset_ripper_dir)
            print("Uninstallation complete.")
        else:
            print(f"AssetRipper directory {asset_ripper_dir} does not exist.")
        return
    
if __name__ == "__main__": # testing
    arh = AssetRipperHandler()
    install_dir = "./asset_ripper"
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        
    arh.get_platform_asset_name()  # Get the platform-specific asset name before usage
    arh.download_latest(install_dir)
    platform_asset_name = arh.get_platform_asset_name()
    if platform_asset_name:
        arh.extract_zip(os.path.join(install_dir, platform_asset_name), install_dir)
        os.remove(os.path.join(install_dir, platform_asset_name))
    else:
        print("Unsupported platform. Exiting.")
