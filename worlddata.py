import os
import requests
from bs4 import BeautifulSoup
import re

FILE_NAME = "output.html"
DIRECTORY = "./webscraping/"

def vrcw_lookup(id): # Ex: wrld_bdba4b66-caca-4ae7-ad11-0336608f7111
    url = f"https://en.vrcw.net/world/detail/{id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Check if the request was successful
        os.makedirs(DIRECTORY, exist_ok=True)  # Create directory if it doesn't exist
        file_path = os.path.join(DIRECTORY, FILE_NAME)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"HTML content saved to {file_path}") # debug, will remove later
        
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
            # print ("/////////////////////////////////////////////////////////")
            # print("World Name: ", world_name + "\n" + "World Description: ", description + "\n" + "World Author: ", author)
            # print ("/////////////////////////////////////////////////////////")
            
            return {"World ID": id, "World Name": world_name, "World Description": description, "World Author": author}
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# exposed function, returns the world name, description, and author in a dictionary
def get_world_info(id):
    data = vrcw_lookup(id)
    if data:
        return data
    else:
        return {"Error": "An error occurred while fetching world data."}