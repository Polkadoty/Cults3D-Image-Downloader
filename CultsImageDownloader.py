import sys, os, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed


def read_creator_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def get_model_links(creator_url, output_file):
    model_links = []
    
    response = requests.get(creator_url)
    if response.status_code != 200:
        print(f"Error fetching creator page: HTTP {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all anchor tags; you might need to adjust the selector to be more specific
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Check if the link is a model link - this condition may need to be updated
        if '/en/3d-model/' in href:
            full_url = urljoin(creator_url, href)
            model_links.append(full_url)
    
    # Append the links to the output file
    with open(output_file, 'a') as file:
        for link in model_links:
            file.write(link + '\n')
    
    return model_links


# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Assume we have a file called 'creator_urls.txt' with one URL per line
creator_urls_file = os.path.join(script_dir, 'creator_urls.txt')
output_file = os.path.join(script_dir, 'model_links.txt')

# Clear the output file before appending new links
open(output_file, 'w').close()

# Read creator URLs from the file and fetch model links for each
creator_urls = read_creator_urls(creator_urls_file)
for url in creator_urls:
    model_links = get_model_links(url, output_file)
    print(f"Found {len(model_links)} model links for {url}.")

print(f"All model links saved to {output_file}.")

def download_image(session, link, img_url, page_folder, i):
    try:
        print(f"Starting download of image {i} from {link}")
        img_response = session.get(img_url, stream=True, timeout=3)
        if img_response.status_code == 200:
            img_filename = f"{link.split('/')[-1]}_{i}.jpg"
            with open(os.path.join(page_folder, img_filename), 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return f"Downloaded image {i} for {link.split('/')[-1]}"
        print(f"Completed download of image {i} from {link}")
    except requests.exceptions.RequestException as e:
        return f"Error downloading image from {img_url}: {e}"
        print(f"Exception downloading image {i} from {link}: {e}")
    except requests.exceptions.Timeout:
        return f"Timeout occurred when downloading image from {img_url}"
        print("Timeout occurred when downloading image from {img_url}")

def download_images(file_links, download_folder):
    os.makedirs(download_folder, exist_ok=True)
    
    # Set up a retry strategy to handle retries with backoff
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # HTTP methods to retry
        backoff_factor=1  # Delay factor for retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    with ThreadPoolExecutor(max_workers=3) as executor:  # Adjust max_workers as necessary
        future_to_url = {}
        
        for link in file_links:
            parsed_url = urlparse(link)
            name = parsed_url.path.split('/')[-1]
            page_folder = os.path.join(download_folder, name)
            os.makedirs(page_folder, exist_ok=True)

            response = session.get(link, timeout=3)
            if response.status_code != 200:
                print(f"Error downloading page {name}: HTTP {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')

            for i, img in enumerate(img_tags):
                img_url = img.attrs.get('src') or img.attrs.get('data-src')
                if img_url and not img_url.startswith(('data:', 'mailto:', 'javascript:')):
                    img_url = urljoin(link, img_url)
                    future = executor.submit(download_image, session, link, img_url, page_folder, i)
                    future_to_url[future] = img_url

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"Error downloading image {url}: {e}")

    print("\nFiles saved to", download_folder)

# Now use the output_file to get the links for downloading images
with open(output_file, 'r') as file:
    file_links = [line.strip() for line in file if line.strip()]

repo_folder = os.path.dirname(os.path.abspath(__file__))
download_folder = os.path.join(repo_folder, "Downloads")
if file_links:
    download_images(file_links, download_folder)
else:
    print("No links to download.")
