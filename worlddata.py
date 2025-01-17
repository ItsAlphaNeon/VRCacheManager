import os
import requests
from bs4 import BeautifulSoup
import traceback

# This whole script will be deprecated in the future, as the VRChat API will be used instead
# I'll just leave this here to use as a fallback in the future if VRChat corperate greed gets in the way

FILE_NAME = "output.html"
DIRECTORY = "./webscraping/"
THUMBNAIL_DIRECTORY = "./assetbundles/thumbnails/"

def vrcw_lookup(id): # Ex: wrld_bdba4b66-caca-4ae7-ad11-0336608f7111
    url = f"https://en.vrcw.net/world/detail/{id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    # Initialize variables to store the world data
    world_name = None
    description = None
    author = None
    thumbnail = None
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the URL: {e}")
        traceback.print_exc()
        return None

    try:
        os.makedirs(DIRECTORY, exist_ok=True)  # Create directory if it doesn't exist
        file_path = os.path.join(DIRECTORY, FILE_NAME)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"HTML content saved to {file_path}") # debug, will remove later
    except OSError as e:
        print(f"An error occurred while saving the HTML content: {e}")
        traceback.print_exc()
        return None

    try:
        # This works, extract data from the HTML file
        with open(file_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
            # Find the world name
            # World name is contained in the only H2 tag in the page
            world_name = soup.h2.text.strip()
            print(f"World name: {world_name}")
            # Find the world description
            description_tag = soup.find("dt", text="Description")
            description = None
            if description_tag:
                description = description_tag.find_next_sibling("dd").text.strip()
                print(f"World description: {description}")
            else:
                print("Description not found")
            # Find the world author
            author_tag = soup.find("dt", text="Author")
            if author_tag:
                author = author_tag.find_next_sibling("dd").text.strip()
                print(f"World author: {author}")
            else:
                print("Author not found")
    except (OSError, AttributeError) as e:
        print(f"An error occurred while parsing the HTML content: {e}")
        traceback.print_exc()
        return None

    try:
        thumbnail_url = f"https://www.vrcw.net/storage/worlds/{id}.png"
        thumbnail_response = requests.get(thumbnail_url, headers=headers, verify=False)
        thumbnail_response.raise_for_status()
        # Save the thumbnail to a file
        os.makedirs(THUMBNAIL_DIRECTORY, exist_ok=True) 
        thumbnail_path = os.path.join(THUMBNAIL_DIRECTORY, f"{id}.png")
        with open(thumbnail_path, "wb") as file:
            file.write(thumbnail_response.content)
        print(f"Thumbnail saved to {thumbnail_path}")  # debug, will remove later
        thumbnail = thumbnail_path
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the thumbnail: {e}")
        traceback.print_exc()
        return None
    except OSError as e:
        print(f"An error occurred while saving the thumbnail: {e}")
        traceback.print_exc()
        return None

    return {"World ID": id, "World Name": world_name, "World Description": description, "World Author": author, "Thumbnail Path": thumbnail}

# exposed function, returns the world name, description, and author in a dictionary
def get_world_info(id):
    data = vrcw_lookup(id)
    if data:
        return data
    else:
        return None