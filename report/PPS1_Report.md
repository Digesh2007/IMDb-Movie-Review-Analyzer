# PPS 1 Report

## IMDb Movie Reviews Web Scraping, Dataset Collection, Cleaning and Processing

### 1. Introduction

This project prepares a structured movie-review dataset for later analysis. PPS 1 covers source-policy checks, collection only when permitted, cleaning, validation, and export. PPS 2 classification is a later stage.

### 2. Problem Statement

Movie reviews must be collected from an authorized source and converted into a consistent dataset before they can be used for sentiment analysis. The project uses Python requests, BeautifulSoup, and pandas while respecting source restrictions.

### 3. Objective

- Select IMDb's Top 100 chart as the intended movie list.
- Collect public movie and review fields only if policy and written permission allow it.
- Preserve separate raw and cleaned copies.
- Remove duplicates, clean text, handle optional missing fields, convert types, validate, and export.

### 4. Tools and Technologies

Python, Requests, BeautifulSoup, pandas, Jupyter Notebook, OpenPyXL, and tqdm.

### 5. Data Source

The policy URL checked by the program is `https://www.imdb.com/robots.txt`. The intended chart URL is `https://www.imdb.com/chart/top/`; it is requested only if policy allows the URL and prior written permission is recorded in the code configuration. Review pages are requested only after the same check. IMDb's policy references `https://www.imdb.com/conditions/`.

IMDb's inspected robots policy states automated data mining/scraping is prohibited without prior written permission and disallows general user agents. Therefore, this project must stop before chart and review requests unless permission and policy conditions change. No chart or review records were collected in the available project run.

### 6. Data Collection Method

The scraper uses a requests Session, clear User-Agent, timeouts, status-code handling, and a delay between requests. It reads robots.txt before target pages, stops on disallow/permission/access errors, and performs no retries or bypasses. BeautifulSoup is configured to parse visible page elements if a permitted response is ever obtained. The selector list is kept in one place for inspection if the public HTML changes.

### 7. Dataset Fields

| Field | Description | Data Type |
| --- | --- | --- |
| `movie_name` | Movie name. | Text |
| `movie_year` | Release year. | Numeric where available |
| `movie_url` | Public movie URL. | URL/text |
| `movie_rating` | Movie rating when available. | Numeric 0–10 |
| `reviewer_username` | Public display name if available. | Text |
| `review_title` | Review headline. | Text |
| `review_text` | Main review body. | Text |
| `review_rating` | Reviewer's rating if available. | Numeric 0–10 |
| `review_date` | Date of review when available. | Date/time |
| `review_url` | Public review URL. | URL/text |
| `scraped_at` | UTC time of collection. | Date/time |

### 8. Data Cleaning

The cleaner prints rows, columns, column names, and the first five records. It removes exact duplicate rows and duplicate reviews by movie name, review title, and review text. It removes HTML, normalizes whitespace, removes records with empty review text, and preserves optional missing fields. Years and ratings are converted to numeric values; rating values outside 0–10 are reported and marked missing. Review and collection dates are parsed where possible. Cleaned CSV and Excel are generated only from an existing raw CSV.

### 9. Dataset Statistics

No data was collected, so statistics remain unavailable and are not invented.

- Total movies: [GENERATED AFTER AUTHORIZED SCRAPING]
- Raw reviews: [GENERATED AFTER AUTHORIZED SCRAPING]
- Cleaned reviews: [GENERATED AFTER CLEANING]
- Duplicates removed: [GENERATED AFTER CLEANING]

### 10. Ethical Considerations

The project checks robots.txt and requires written permission before automated collection. It uses a clear User-Agent and reasonable delays, stops on restrictions, and does not bypass CAPTCHA, logins, paywalls, access controls, or rate limits. It avoids unnecessary personal/sensitive reviewer information. Data collection has not proceeded under the current published policy.

### 11. Limitations

- Website page structure and selectors can change.
- Public data availability and access policies can change.
- Public review pages may not expose all fields.
- Authorization, robots rules, and rate limits can prevent collection.
- No collected dataset means PPS 2 cannot yet be trained or evaluated.

### 12. Conclusion

The code and notebook document a compliant PPS 1 workflow and stop when access is not allowed. Dataset outputs and statistics remain ungenerated. After written permission and permitted access are obtained, actual records can be collected, cleaned, and used for PPS 2 sentiment classification.