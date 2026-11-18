import requests
import os

url = input("Enter the Download Link")

try:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()

        with open("largefile.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print("Download complete")

    # Shutdown after 60 seconds
    #os.system("shutdown /s /t 60")

except requests.exceptions.RequestException as e:
    print("Download failed!")
    print(e)