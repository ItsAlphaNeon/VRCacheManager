import requests
import zipfile
import os
import threading

class AssetRipperHandler:
    def __init__(self):
        pass
    
    def download_latest(self, install_dir):
        api_url = "https://api.github.com/repos/AssetRipper/AssetRipper/releases/latest"
        response = requests.get(api_url)
        if response.status_code == 200:
            latest_release = response.json()
            download_url = None
            for asset in latest_release['assets']:
                if asset['name'] == 'AssetRipper_win_x64.zip':
                    download_url = asset['browser_download_url']
                    break
            if download_url:
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    with open(os.path.join(install_dir, 'AssetRipper_win_x64.zip'), 'wb') as file:
                        file.write(download_response.content)
                else:
                    print("Failed to download the asset ripper.")
            else:
                print("AssetRipper_win_x64.zip not found in the latest release.")
        else:
            print("Failed to fetch the latest release information.")
        return
    
    def extract_zip(self, zip_path, extract_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return
    
    def uninstall_asset_ripper(self, install_dir):
        asset_ripper_dir = os.path.join(install_dir, 'AssetRipper_win_x64')
        if os.path.exists(asset_ripper_dir):
            os.rmdir(asset_ripper_dir)
        return
    
if __name__ == "__main__": # Debugging
    arh = AssetRipperHandler()
    install_dir = "./asset_ripper"
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
    arh.download_latest(install_dir)
    arh.extract_zip(os.path.join(install_dir, 'AssetRipper_win_x64.zip'), install_dir)
    os.remove(os.path.join(install_dir, 'AssetRipper_win_x64.zip'))
    print("AssetRipper installed successfully.")