from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
# Removed unused import
from vrchatapi.api.worlds_api import WorldsApi
from PyQt6.QtCore import pyqtSignal, QObject
import vrchatapi
import os
# Removed unused import
import requests
from vrchatapi.rest import ApiException

# This is for our legacy conversion where we save thumbnails locally
THUMBNAIL_DIRECTORY = "./assetbundles/thumbnails/"

class VRChatAPIManager(QObject):
    username_password_signal = pyqtSignal()
    two_factor_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.configuration = vrchatapi.Configuration()

    def authenticate(self, username, password, api_usage_email="vrc@freevrc.com"):
        # Ensure a properly formatted user-agent
        user_agent = f"VRCM/0.0.1 {api_usage_email}"
        print("User-Agent:", user_agent) # debug, will remove later
        self.configuration.user_agent = user_agent

        if username and password:
            self.configuration.username = username
            self.configuration.password = password

            try:
                with vrchatapi.ApiClient(self.configuration) as api_client:
                    auth_api = authentication_api.AuthenticationApi(api_client)
                    current_user = auth_api.get_current_user()
                    print("Logged in as:", current_user.display_name)
            except UnauthorizedException as e:
                self.handle_unauthorized_exception(e)
            except vrchatapi.ApiException as e:
                print("Exception when calling API: %s\n", e)
                
        print("Authentication complete")

    def handle_unauthorized_exception(self, e):
        if e.status == 200:
            if "Email 2 Factor Authentication" in e.reason:
                self.two_factor_signal.emit("Email 2FA Code:")
            elif "2 Factor Authentication" in e.reason:
                self.two_factor_signal.emit("2FA Code:")
        else:
            print("Exception when calling API: %s\n", e)

    def verify_two_factor_code(self, code):
        try:
            with vrchatapi.ApiClient(self.configuration) as api_client:
                auth_api = authentication_api.AuthenticationApi(api_client)
                auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(code))
                current_user = auth_api.get_current_user()
                print("Logged in as:", current_user.display_name)
        except vrchatapi.ApiException as e:
            print("Exception when calling API: %s\n", e)

    def get_world_from_id(self, world_id): # This returns the JSON from the API. We'll need to clean that up to integrate in the GUI part
        try:
            with vrchatapi.ApiClient(self.configuration) as api_client:
                api_client.user_agent = f"VRCM/0.0.1 vrc@freevrc.com"
                world_api = WorldsApi(api_client)
                world = world_api.get_world(world_id)
                return world
        except vrchatapi.ApiException as e:
            print("Exception when calling API: %s\n", e)
            return None
        
    def get_legacy_format_world_info(self, world_JSON):
        print("get_legacy_format_world_info: "+ str(world_JSON)) # debug, will remove later
        try:
            if not world_JSON.id:
                # This is not a valid world JSON
                return None
        except AttributeError:
            # Handle the case where world_JSON does not have an 'id' attribute
            print("Invalid world JSON: missing 'id' attribute")
            return None
        world_id = world_JSON.id
        world_name = world_JSON.name
        world_description = world_JSON.description
        world_author = world_JSON.author_name
        thumbnail_url = world_JSON.thumbnail_image_url

        # Save thumbnail locally
        os.makedirs(THUMBNAIL_DIRECTORY, exist_ok=True)
        thumbnail_path = os.path.join(THUMBNAIL_DIRECTORY, f"{world_id}.png")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        try:
            thumbnail_response = requests.get(thumbnail_url, headers=headers)
            thumbnail_response.raise_for_status()
            with open(thumbnail_path, "wb") as file:
                file.write(thumbnail_response.content)
            print(f"Thumbnail saved to {thumbnail_path}")  # debug, will remove later
        except requests.RequestException as e:
            print(f"Failed to download thumbnail: {e}")
            thumbnail_path = None

        return {
            "World ID": world_id,
            "World Name": world_name,
            "World Description": world_description,
            "World Author": world_author,
            "Thumbnail Path": thumbnail_path
        }

# if __name__ == "__main__":
#     api_manager = VRChatAPIManager()
#     api_manager.authenticate(None, None, "vrc@freevrc.com")
#     worldid = 'wrld_2dddec3a-f471-4c7e-ab39-00ab9ce427c7'
#     worldJSON = api_manager.get_world_from_id(worldid)
#     print("get_world_from_id: "+ str(worldJSON))
#     print("get_legacy_format_world_info: " + str(api_manager.get_legacy_format_world_info(worldJSON)))