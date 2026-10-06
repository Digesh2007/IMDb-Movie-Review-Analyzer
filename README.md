# IMDb Movie Review Analyzer

Beginner-friendly project workspace for PPS 1 data collection and cleaning, with a separate PPS 2 training scaffold. The dashboard is static HTML/CSS/JavaScript; the Python scripts handle dataset collection, cleaning, and (only when a labeled dataset exists) sentiment-model evaluation.

## Current Project Status

The inspected IMDb `robots.txt` says automated data mining/scraping requires prior written permission and disallows general user agents. The scraper checks the policy and stops before it requests chart or review pages unless the rules permit access and the permission flag is explicitly enabled. No raw or cleaned data files are supplied or fabricated. Therefore, PPS 1 collection and PPS 2 training/evaluation are not completed yet.

## Project Structure

```text
IMDb_Movie_Review_Project/
├── assets/
│   ├── app.js
│   └── styles.css
├── data/
│   ├── raw_imdb_reviews.csv                 # generated only from permitted collection
│   ├── cleaned_imdb_reviews.csv             # generated from raw data
│   ├── cleaned_imdb_reviews.xlsx            # generated from raw data
│   └── sentiment_model_metrics.csv          # generated after actual PPS 2 training
├── notebooks/
│   └── IMDb_Movie_Reviews_PPS1.ipynb
├── report/
│   └── PPS1_Report.md
├── src/
│   ├── imdb_scraper.py
│   ├── clean_imdb_reviews.py
│   └── sentiment_analysis.py
├── index.html
├── requirements.txt
├── README.md
└── .gitignore
```

## Install Python Dependencies

From Windows PowerShell in the project folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The dashboard itself needs no Python packages. The Python scripts require the packages listed in `requirements.txt`.

## PPS 1: Collection and Cleaning

The selected target is the **Top 100** chart: `https://www.imdb.com/chart/top/`. The program first checks `https://www.imdb.com/robots.txt`. IMDb's published policy requires prior written permission for automated collection and currently disallows general-agent access. The script will stop if collection is disallowed or written permission is not recorded. It does not bypass CAPTCHA, login, access control, rate limits, or use private APIs.

When collection is legally and technically permitted and written permission is obtained, run:

```powershell
python src/imdb_scraper.py
```

If a genuine raw file exists, clean it separately:

```powershell
python src/clean_imdb_reviews.py
```

Outputs are `data/raw_imdb_reviews.csv`, `data/cleaned_imdb_reviews.csv`, and `data/cleaned_imdb_reviews.xlsx`. Files are not created as placeholders. Cleaning removes duplicates, strips HTML, normalizes whitespace, drops only rows with empty review text, converts years/ratings/dates, and reports/marks ratings outside 0–10 as missing.

### Dataset Fields

| Field | Meaning |
| --- | --- |
| `movie_name` | Movie name. |
| `movie_year` | Movie release year. |
| `movie_url` | Public IMDb movie URL. |
| `movie_rating` | Movie rating, when available. |
| `reviewer_username` | Public reviewer name/display name, when available. |
| `review_title` | Review headline. |
| `review_text` | Review body. |
| `review_rating` | Reviewer's numeric rating, when available. |
| `review_date` | Review date, when available. |
| `review_url` | Public review URL. |
| `scraped_at` | UTC collection timestamp. |

## PPS 2: Sentiment Classification (Not Yet Run)

PPS 2 requires a genuine cleaned dataset and a defensible label column. `src/sentiment_analysis.py` is a guarded scaffold that refuses to train without usable records. It can use an existing `sentiment` column containing only `positive`/`negative`; alternatively, it documents a review-rating proxy: ratings 7–10 are positive, 0–4 negative, and 5–6 are excluded as ambiguous. This is a proxy, not human-verified sentiment. Reviewers should approve the labeling rule before reporting it.

After PPS 1 is complete and `sentiment` labels are present or rating-derived, run:

```powershell
python src/sentiment_analysis.py
```

The script uses a stratified train/test split, TF-IDF with lowercase, tokenization and English stop-word removal, then compares Logistic Regression, Multinomial Naive Bayes, Decision Tree, Random Forest, and linear SVM. It calculates accuracy, precision, recall, F1, and confusion matrices from the actual holdout predictions. It does not print made-up scores. Stemming/lemmatization is not added by default; it should only be included if justified and compared on real data.

## Dashboard

Start the local static site:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000`, then stop with `Ctrl+C`. The Dataset view imports a local CSV into the browser for preview/cleaning/export; it does not fetch IMDb. No records, sentiment labels, or model results are preloaded.

## Notebook

```powershell
jupyter notebook notebooks/IMDb_Movie_Reviews_PPS1.ipynb
```

The notebook documents the PPS 1 workflow and reports the current access restriction. It contains no PPS 2 classification code.

## Ethical Scraping

Read IMDb's robots policy and Conditions of Use before any collection. Do not scrape unless written permission and the current policy both allow it. Use a clear User-Agent and reasonable delays. Stop on access restrictions; never bypass anti-bot checks or gather unnecessary personal/sensitive information.

## Viva Preparation

1. **What is web scraping?** Programmatically collecting information from web pages when the website permits it.
2. **Why use requests?** It sends HTTP requests and receives server responses.
3. **What is BeautifulSoup?** A library that parses HTML and helps find visible page elements.
4. **Why pandas?** It organizes records in tables and supports data cleaning and exports.
5. **What is HTML parsing?** Reading the structure of HTML to locate page content.
6. **What is a User-Agent?** A request header identifying the software making a request.
7. **Why respect robots.txt?** It communicates crawling rules for automated clients.
8. **Why add delays?** To limit request rate and reduce unnecessary server load.
9. **What is a DataFrame?** A two-dimensional table in pandas.
10. **Why remove duplicates?** To avoid repeated records affecting counts and analysis.
11. **How are missing values handled?** Optional fields are preserved; rows without review text are removed for review analysis.
12. **Why remove HTML?** Markup is not part of the readable review body.
13. **Why convert ratings to numbers?** Numeric values can be checked and analyzed mathematically.
14. **What is preprocessing?** Cleaning and formatting data before analysis.
15. **Raw versus cleaned data?** Raw is the collected copy; cleaned data has duplicates and formatting issues handled.
16. **Why IMDb?** It is the assignment's named data source.
17. **What happens in PPS 2?** Properly labeled cleaned review text is used to train and evaluate classifiers.
18. **What is sentiment classification?** Assigning text to sentiment categories such as positive or negative.
19. **Why not bypass CAPTCHA?** It is a technical access restriction and must be respected.
20. **What limits scraping?** Changing pages, incomplete public fields, authorization, robots rules, and rate limits.
