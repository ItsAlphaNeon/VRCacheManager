import os

class AssetBundleManager:
    def __init__(self):
        self.verify_integrity()

    def copy_asset_bundle(self, src, dest, rename=""):
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source file {src} does not exist.")

        if not os.path.exists(dest):
            os.makedirs(dest)

        base_name = os.path.basename(src)
        if rename:
            base_name = rename

        dest_path = os.path.join(dest, base_name)

        with open(src, "rb") as fsrc:
            with open(dest_path, "wb") as fdest:
                fdest.write(fsrc.read())

        print(f"Copied {src} to {dest_path}")

    def rename_asset_bundle(self, src, dest):
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source file {src} does not exist.")

        if not os.path.exists(dest):
            os.makedirs(dest)

        base_name = os.path.basename(src)
        dest_path = os.path.join(dest, base_name)

        os.rename(src, dest_path)

        print(f"Renamed {src} to {dest_path}")

    def verify_integrity(self):
        if not os.path.exists("assetbundles"):
            os.makedirs("assetbundles")

    def get_asset_bundle_size(self, path):
        return os.path.getsize(path)
