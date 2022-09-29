import sys
import os
import requests
import re

if len(sys.argv) != 2:
    url = input("Enter the URL of the model: ")
else:
    url = sys.argv[1]
    
req = requests.get(url)

if req.status_code != 200:
    sys.exit("Error : HTTP response code " + str(req.status_code))
    
cut_response = req.text.split('<h2 class="t1">Creator</h2>', 1)[0]

image_urls = list(set(result for result in re.findall(r'/(https?://[^\s/]+/[^\s/]+/[^\s/]+/[^\s/]+/[^\s/]+/[^\s/"]+)"', cut_response)))

preview_urls = list(set(result for result in re.findall(r'href=[^\s]+/(https://preview3d-images.cults3d.com/[^\s/"]+)"', cut_response)))

if len(image_urls) != 0:
    print("\nImage links")
    for link in image_urls:
        print(link)

if len(preview_urls) != 0:
    print("\nPreview image links")
    for link in preview_urls:
        print(link)
    
if len(image_urls) > 0 or len(preview_urls) > 0:
    download = input("\nWould you like to download these files? (y/n) ")
else:
    sys.exit()

if download.lower() in ['y', 'yes']:

    current_folder = os.getcwd()
    new_folder = os.path.join(current_folder, url.split("/")[-1])
    os.makedirs(new_folder, exist_ok=True)
    print()

    for link in image_urls:
        name = link.split("/")[-1]
        file = open(os.path.join(new_folder, name), "ab")
        file.write(requests.get(link).content)
        file.close()
        print("Downloaded ", name)
    
    count = 1
    for link in preview_urls:
        name = "Preview-" + str(count) + ".png"
        file = open(os.path.join(new_folder, name), "ab")
        file.write(requests.get(link).content)
        file.close()
        print("Downloaded ", name)
        count += 1
        
    print("\nFiles saved to " + new_folder)