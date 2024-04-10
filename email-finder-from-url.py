import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urljoin, urlparse, urlunparse

# Configuration
input_file = "url.csv"
output_file = "emails_found.csv"
max_depth = 13  # Maximum depth of crawling

# Regular expression for finding emails
email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def find_emails_in_text(text):
    """Find emails in a given piece of text."""
    return set(email_regex.findall(text))

def normalize_url(url):
    """Normalize a URL by removing the fragment and query."""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment="", query=""))

def detect_repeated_segments(path):
    """Check if a URL path segment is repeated (indicative of a loop)."""
    segments = path.strip('/').split('/')
    return any(segments.count(segment) > 1 for segment in segments)

def get_domain(url):
    """Extract domain from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc

def crawl(start_url, visited_urls, emails_found, depth=0):
    """Crawl a webpage and extract emails, with depth limiting."""
    if depth > max_depth:
        print("Reached max depth")
        return

    domain = get_domain(start_url)
    normalized_url = normalize_url(start_url)
    if normalized_url in visited_urls or detect_repeated_segments(urlparse(normalized_url).path):
        return

    print(f"Visiting: {normalized_url}")
    visited_urls.add(normalized_url)

    try:
        response = requests.get(normalized_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        emails = find_emails_in_text(response.text)
        emails_found.update(emails)

        for link in soup.find_all('a', href=True):
            href = link['href']
            next_url = urljoin(normalized_url, href)
            next_url = normalize_url(next_url)
            if get_domain(next_url) == domain:
                crawl(next_url, visited_urls, emails_found, depth + 1)
    except Exception as e:
        print(f"Failed to access {normalized_url}: {str(e)}")

def read_websites_from_csv(filename):
    """Read website URLs from a CSV file."""
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        return [row[0] for row in reader]

def save_emails_to_csv(emails, filename):
    """Save found emails to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for email in emails:
            writer.writerow([email])

# Main execution
visited_urls = set()
emails_found = set()

websites = read_websites_from_csv(input_file)
for website in websites:
    visited_urls.clear()  # Clear visited URLs for each website
    crawl(website, visited_urls, emails_found)

save_emails_to_csv(emails_found, output_file)

print(f"Finished crawling. Found {len(emails_found)} emails. Saved to {output_file}.")
