"""Clean a genuine raw CSV into separate CSV and Excel outputs."""

from pathlib import Path
import re

import pandas as pd
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw_imdb_reviews.csv"
CLEANED_CSV_PATH = PROJECT_ROOT / "data" / "cleaned_imdb_reviews.csv"
CLEANED_EXCEL_PATH = PROJECT_ROOT / "data" / "cleaned_imdb_reviews.xlsx"
TEXT_COLUMNS = [
    "movie_name",
    "movie_url",
    "reviewer_username",
    "review_title",
    "review_text",
    "review_url",
]
RATING_COLUMNS = ["movie_rating", "review_rating"]
DATE_COLUMNS = ["review_date", "scraped_at"]


def clean_text(value):
    """Remove HTML markup and normalize whitespace while preserving missing data."""
    if pd.isna(value):
        return pd.NA
    visible_text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", visible_text).strip()


def clean_dataset(
    raw_path=RAW_CSV_PATH,
    cleaned_csv_path=CLEANED_CSV_PATH,
    cleaned_excel_path=CLEANED_EXCEL_PATH,
):
    """Clean a raw CSV, retaining optional missing values and exporting both formats."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {raw_path}. No example dataset was created."
        )

    dataframe = pd.read_csv(raw_path)
    print(f"Raw rows: {len(dataframe)}")
    print(f"Raw columns: {len(dataframe.columns)}")
    print(f"Column names: {list(dataframe.columns)}")
    print("First five rows:")
    print(dataframe.head())

    exact_before = len(dataframe)
    dataframe = dataframe.drop_duplicates().copy()
    exact_duplicates_removed = exact_before - len(dataframe)

    for column in TEXT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].map(clean_text)

    if "review_text" in dataframe.columns:
        review_text = dataframe["review_text"].fillna("").astype(str).str.strip()
        missing_review_text = int(review_text.eq("").sum())
        dataframe = dataframe.loc[review_text.ne("")].copy()
    else:
        missing_review_text = len(dataframe)
        dataframe = dataframe.iloc[0:0].copy()

    review_key = [
        column
        for column in ("movie_name", "review_title", "review_text")
        if column in dataframe.columns
    ]
    before_review_deduplication = len(dataframe)
    if review_key:
        dataframe = dataframe.drop_duplicates(subset=review_key).copy()
    duplicate_reviews_removed = before_review_deduplication - len(dataframe)

    if "movie_year" in dataframe.columns:
        dataframe["movie_year"] = pd.to_numeric(dataframe["movie_year"], errors="coerce")

    invalid_ratings = {}
    for column in RATING_COLUMNS:
        if column not in dataframe.columns:
            continue
        numeric_rating = pd.to_numeric(dataframe[column], errors="coerce")
        invalid_mask = numeric_rating.notna() & ~numeric_rating.between(0, 10)
        invalid_values = numeric_rating.loc[invalid_mask].unique().tolist()
        invalid_ratings[column] = {"count": int(invalid_mask.sum()), "values": invalid_values}
        if invalid_mask.any():
            print(f"{column}: invalid values {invalid_values}; marking them missing.")
            numeric_rating.loc[invalid_mask] = pd.NA
        dataframe[column] = numeric_rating

    for column in DATE_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column], errors="coerce", utc=True
            ).dt.tz_convert(None)

    cleaned_csv_path = Path(cleaned_csv_path)
    cleaned_excel_path = Path(cleaned_excel_path)
    cleaned_csv_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_excel_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(cleaned_csv_path, index=False)
    dataframe.to_excel(cleaned_excel_path, index=False)

    exact_total = exact_duplicates_removed + duplicate_reviews_removed
    print(f"Exact duplicate rows removed: {exact_duplicates_removed}")
    print(f"Duplicate reviews removed: {duplicate_reviews_removed}")
    print(f"Rows with empty review text removed: {missing_review_text}")
    print(f"Cleaned rows saved: {len(dataframe)}")
    return {
        "dataframe": dataframe,
        "exact_duplicates_removed": exact_duplicates_removed,
        "duplicate_reviews_removed": duplicate_reviews_removed,
        "duplicates_removed": exact_total,
        "missing_review_text": missing_review_text,
        "invalid_ratings": invalid_ratings,
    }


if __name__ == "__main__":
    try:
        clean_dataset()
    except FileNotFoundError as error:
        print(error)