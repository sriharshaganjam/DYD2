# scraper.py
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# Load URLs from scrape_urls.json
with open("scrape_urls.json") as f:
    url_config = json.load(f)
urls = url_config["urls"]

def extract_courses_from_url(url):
    print(f"Scraping {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    course_data = []
    degree = soup.find("h1") or soup.title
    degree_name = degree.get_text(strip=True) if degree else "Unknown Degree"

    # Find course blocks (change as per site structure)
    course_blocks = soup.find_all(["h3", "h4", "li", "p"])
    for block in course_blocks:
        text = block.get_text(strip=True)
        if not text or len(text.split()) < 3:
            continue  # Skip short or meaningless entries
        course_data.append({
            "degree": degree_name,
            "course": text,
            "subjects": [],  # Optional: fill using nested pages if any
            "source_url": url
        })

    return course_data

# Main scrape
all_data = []
for url in urls:
    try:
        data = extract_courses_from_url(url)
        all_data.extend(data)
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

# Save output
with open("courses.json", "w") as f:
    json.dump(all_data, f, indent=2)

print("Scraping complete. Data saved to courses.json")
