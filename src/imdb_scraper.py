"""PPS 1 IMDb collector: checks policy and stops when collection is disallowed."""

from datetime import datetime, timezone
from pathlib import Path
import random
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_CSV_PATH = DATA_DIR / "raw_imdb_reviews.csv"
TOP_MOVIES_URL = "https://www.imdb.com/chart/top/"
ROBOTS_URL = "https://www.imdb.com/robots.txt"
IMDB_HOSTS = {"imdb.com", "www.imdb.com"}
USER_AGENT = "IMDbReviewPPS1/1.0 (student project; no contact supplied)"
REQUEST_TIMEOUT = 15
MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 5
WRITTEN_PERMISSION_GRANTED = False

DATASET_COLUMNS = [
    "movie_name",
    "movie_year",
    "movie_url",
    "movie_rating",
    "reviewer_username",
    "review_title",
    "review_text",
    "review_rating",
    "review_date",
    "review_url",
    "scraped_at",
]

# Keep selectors together so authorized future maintenance stays easy to inspect.
MOVIE_ITEM_SELECTOR = "li.ipc-metadata-list-summary-item"
REVIEW_CARD_SELECTORS = ["[data-testid='review-card']", "div.review-container"]

session = requests.Session()
session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }
)
_robots_parser = None
_last_request_at = 0.0


class CollectionStopped(Exception):
    """Expected policy, access, or page-structure stop condition."""


def clean_text(value):
    """Remove HTML tags and normalize whitespace in a visible text value."""
    if value is None:
        return ""
    visible_text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", visible_text).strip()


def wait_between_requests():
    """Use a modest randomized delay between HTTP requests."""
    global _last_request_at
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    elapsed = time.monotonic() - _last_request_at
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request_at = time.monotonic()


def get_robots_policy():
    """Fetch robots.txt once so target pages can be checked before requesting."""
    global _robots_parser
    if _robots_parser is not None:
        return _robots_parser

    wait_between_requests()
    try:
        response = session.get(ROBOTS_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.Timeout as error:
        raise CollectionStopped("Timed out while checking IMDb robots.txt.") from error
    except requests.ConnectionError as error:
        raise CollectionStopped("Could not connect to check IMDb robots.txt.") from error
    except requests.RequestException as error:
        raise CollectionStopped(f"Could not check IMDb robots.txt: {error}") from error

    parser = RobotFileParser(ROBOTS_URL)
    parser.parse(response.text.splitlines())
    _robots_parser = parser
    return parser


def safe_get(url):
    """Request one IMDb page only when policy and written permission allow it."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in IMDB_HOSTS:
        raise CollectionStopped("Stopped: only IMDb HTTPS pages are allowed.")

    if not get_robots_policy().can_fetch(USER_AGENT, url):
        raise CollectionStopped(
            "IMDb robots.txt disallows this page for the project User-Agent. "
            "No movie or review page was requested."
        )
    if not WRITTEN_PERMISSION_GRANTED:
        raise CollectionStopped(
            "IMDb's published policy requires prior written permission for automated "
            "collection. No movie or review page was requested."
        )

    wait_between_requests()
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.Timeout as error:
        raise CollectionStopped(f"Request timed out: {url}") from error
    except requests.ConnectionError as error:
        raise CollectionStopped(f"Connection failed: {url}") from error
    except requests.RequestException as error:
        raise CollectionStopped(f"Request failed: {error}") from error

    if response.status_code in {401, 403, 429}:
        raise CollectionStopped(
            f"IMDb returned HTTP {response.status_code}; collection stopped without retrying."
        )
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise CollectionStopped(f"IMDb returned HTTP {response.status_code}.") from error

    lowered_page = response.text.lower()
    if "captcha" in lowered_page or "robot check" in lowered_page:
        raise CollectionStopped("An anti-bot challenge was shown; collection stopped.")
    return response


def _find_text(element, selectors):
    for selector in selectors:
        match = element.select_one(selector)
        if match:
            text = clean_text(match.get_text(" ", strip=True))
            if text:
                return text
    return ""


def get_top_movies(limit=100):
    """Read movie names, years, ratings, and links from the public chart HTML."""
    response = safe_get(TOP_MOVIES_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    movie_items = soup.select(MOVIE_ITEM_SELECTOR)
    if not movie_items:
        raise CollectionStopped(
            "The public chart HTML did not match the configured selectors. "
            "No data was saved; inspect permitted HTML before updating selectors."
        )

    movies = []
    for item in movie_items[:limit]:
        link = item.select_one("a.ipc-title-link-wrapper[href], h3 a[href], a[href*='/title/']")
        if not link:
            continue
        movie_url = urljoin("https://www.imdb.com", link.get("href", "").split("?")[0])
        if "/title/" not in urlparse(movie_url).path:
            continue
        text = clean_text(item.get_text(" ", strip=True))
        year = re.search(r"\b(?:18|19|20)\d{2}\b", text)
        name = re.sub(r"^\d+\.\s*", "", clean_text(link.get_text(" ", strip=True)))
        movies.append(
            {
                "movie_name": name,
                "movie_year": year.group(0) if year else "",
                "movie_url": movie_url,
                "movie_rating": _find_text(item, ["span.ipc-rating-star--rating"]),
            }
        )
    if not movies:
        raise CollectionStopped("No movie entries were found in the public chart HTML.")
    return movies


def get_movie_details(movie_url):
    """Read a movie title page when policy and permission allow it."""
    response = safe_get(movie_url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = _find_text(soup, ["h1[data-testid='hero__pageTitle']", "h1"])
    page_text = clean_text(soup.get_text(" ", strip=True))
    year = re.search(r"\b(?:18|19|20)\d{2}\b", page_text)
    return {
        "movie_name": title,
        "movie_year": year.group(0) if year else "",
        "movie_url": movie_url,
        "movie_rating": _find_text(soup, ["span.ipc-rating-star--rating"]),
    }


def get_movie_reviews(movie_url, movie_name="", movie_year="", movie_rating=""):
    """Extract review fields visible in a permitted public reviews page."""
    review_url = urljoin(movie_url.rstrip("/") + "/", "reviews/")
    response = safe_get(review_url)
    soup = BeautifulSoup(response.text, "html.parser")
    cards = []
    for selector in REVIEW_CARD_SELECTORS:
        cards = soup.select(selector)
        if cards:
            break

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records = []
    for card in cards:
        title_element = card.select_one(
            "[data-testid='review-title'], a.title, h3 a[href*='/review/']"
        )
        review_link = title_element or card.select_one("a[href*='/review/']")
        public_review_url = (
            urljoin("https://www.imdb.com", review_link.get("href", ""))
            if review_link
            else ""
        )
        records.append(
            {
                "movie_name": movie_name,
                "movie_year": movie_year,
                "movie_url": movie_url,
                "movie_rating": movie_rating,
                "reviewer_username": _find_text(
                    card, ["a.user-name", "[data-testid='author-link']"]
                ),
                "review_title": clean_text(title_element.get_text(" ", strip=True))
                if title_element
                else "",
                "review_text": _find_text(
                    card,
                    [
                        "[data-testid='review-overflow']",
                        "div.text.show-more__control",
                        "div.ipc-html-content-inner-div",
                    ],
                ),
                "review_rating": _find_text(
                    card,
                    ["span.rating-other-user-rating span", "span.ipc-rating-star--rating"],
                ),
                "review_date": _find_text(
                    card, ["span.review-date", "[data-testid='review-date']"]
                ),
                "review_url": public_review_url,
                "scraped_at": scraped_at,
            }
        )
    return records


def save_raw_dataset(records, output_path=RAW_CSV_PATH):
    """Save only real extracted rows; never create an empty or sample dataset."""
    if not records:
        print("No review records collected; raw CSV was not created.")
        return None
    dataframe = pd.DataFrame(records, columns=DATASET_COLUMNS).drop_duplicates()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    print(f"Saved {len(dataframe)} raw review records to {output_path}")
    return dataframe


def collect_dataset(limit=100):
    """Collect up to 100 movies and visible reviews if access is allowed."""
    movies = get_top_movies(limit=limit)
    print(f"Movies found: {len(movies)}")
    records = []
    for movie in tqdm(movies, desc="Collecting permitted reviews"):
        records.extend(
            get_movie_reviews(
                movie["movie_url"],
                movie["movie_name"],
                movie["movie_year"],
                movie["movie_rating"],
            )
        )
    raw_dataframe = save_raw_dataset(records)
    return movies, raw_dataframe


if __name__ == "__main__":
    try:
        collect_dataset(limit=100)
    except CollectionStopped as error:
        print(f"Collection stopped safely: {error}")