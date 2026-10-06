"""PPS 2 scaffold; trains only when genuine review text and labels are available."""

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_CSV_PATH = PROJECT_ROOT / "data" / "cleaned_imdb_reviews.csv"
METRICS_PATH = PROJECT_ROOT / "data" / "sentiment_model_metrics.csv"
TEXT_COLUMN = "review_text"
LABEL_COLUMN = "sentiment"


def prepare_labels(dataframe):
    """Use explicit labels or documented review-rating proxy labels.

    The proxy treats ratings 7-10 as positive and 0-4 as negative.
    Ratings 5-6 are excluded as ambiguous. This is not human-verified sentiment.
    """
    data = dataframe.copy()
    if LABEL_COLUMN in data.columns:
        data[LABEL_COLUMN] = data[LABEL_COLUMN].astype("string").str.lower().str.strip()
        data = data[data[LABEL_COLUMN].isin(["positive", "negative"])].copy()
    elif "review_rating" in data.columns:
        ratings = pd.to_numeric(data["review_rating"], errors="coerce")
        data = data[ratings.between(0, 10)].copy()
        ratings = ratings.loc[data.index]
        data[LABEL_COLUMN] = pd.NA
        data.loc[ratings >= 7, LABEL_COLUMN] = "positive"
        data.loc[ratings <= 4, LABEL_COLUMN] = "negative"
        data = data[data[LABEL_COLUMN].notna()].copy()
        print(
            "Labels derived from actual reviewer ratings: 7-10 positive, "
            "0-4 negative, 5-6 omitted. This is a rating proxy, not verified sentiment."
        )
    else:
        raise ValueError(
            "Add a sentiment column (positive/negative) or provide review_rating "
            "so the documented rating proxy can be applied."
        )

    data[TEXT_COLUMN] = data[TEXT_COLUMN].fillna("").astype(str).str.strip()
    return data[data[TEXT_COLUMN].ne("")].copy()


def train_and_compare(dataframe):
    """Train five text classifiers and return metrics from held-out predictions."""
    data = prepare_labels(dataframe)
    counts = data[LABEL_COLUMN].value_counts()
    if set(counts.index) != {"positive", "negative"} or counts.min() < 2:
        raise ValueError(
            "Training needs at least two genuine examples in each sentiment class."
        )

    features = data[TEXT_COLUMN]
    labels = data[LABEL_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Naive Bayes": MultinomialNB(),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "SVM": LinearSVC(random_state=42),
    }
    results = []
    for model_name, classifier in classifiers.items():
        model = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        stop_words="english",
                        token_pattern=r"(?u)\b\w\w+\b",
                    ),
                ),
                ("classifier", classifier),
            ]
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test,
            predictions,
            average="binary",
            pos_label="positive",
            zero_division=0,
        )
        results.append(
            {
                "model": model_name,
                "accuracy": accuracy_score(y_test, predictions),
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "confusion_matrix": confusion_matrix(
                    y_test, predictions, labels=["negative", "positive"]
                ).tolist(),
            }
        )
    return results


if __name__ == "__main__":
    if not CLEANED_CSV_PATH.exists():
        print(
            "PPS 2 not run: cleaned CSV is missing. Complete authorized PPS 1 "
            "collection and cleaning first."
        )
    else:
        try:
            cleaned_data = pd.read_csv(CLEANED_CSV_PATH)
            model_results = train_and_compare(cleaned_data)
            results_table = pd.DataFrame(model_results).drop(columns="confusion_matrix")
            METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
            results_table.to_csv(METRICS_PATH, index=False)
            print(results_table.to_string(index=False))
            best_result = max(model_results, key=lambda item: item["f1_score"])
            print(f"Best model by test F1: {best_result['model']}")
            for result in model_results:
                print(f"{result['model']} confusion matrix: {result['confusion_matrix']}")
            print(f"Metrics saved to {METRICS_PATH}")
        except (ValueError, KeyError) as error:
            print(f"PPS 2 not run: {error}")