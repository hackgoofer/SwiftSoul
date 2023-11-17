from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Setup the selenium driver
driver = webdriver.Chrome()  # or use the appropriate driver for your browser
driver.get(
    "https://kworb.net/youtube/artist/taylorswift.html"
)  # replace with the actual website URL

# Find all the <a> tags with "/video/" in their href attribute
video_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
urls_and_names = [
    (video.get_attribute("href"), video.get_attribute("innerHTML").strip())
    for video in video_links
]

print(urls_and_names)

# Initialize a list to store tuples of (url, name)
video_details = []

# Iterate over the found <a> tags
for video_url, video_name in urls_and_names:
    url = video_url.split("/")[-1].split(".")[0]
    video_details.append(("https://youtu.be/" + url, video_name))
    print(f"done: {video_name}, url: {video_url}")

driver.quit()  # Close the browser

# Now video_details contains all the (url, name) tuples
with open("metadata2.txt", "w") as f:
    for detail in video_details:
        f.write(f"{detail[0]}, {detail[1]}\n")
