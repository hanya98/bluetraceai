from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    classification_report,
)
from xgboost import XGBClassifier


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "data" / "xgboost_features.csv"
MODEL_FILE = BASE_DIR / "xgboost_attribution_model.json"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("LOADING XGBOOST DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# ONLY USE SPILLS WITH A GENUINE POSITIVE
# ============================================================

spill_summary = (
    df.groupby("spill_id")["label"]
    .agg(["count", "sum"])
    .sort_index()
)

print("\nSpill summary:")
print(spill_summary)


usable_spills = spill_summary[
    spill_summary["sum"] > 0
].index.tolist()

excluded_spills = spill_summary[
    spill_summary["sum"] == 0
].index.tolist()

print("\nUsable spills:")
for s in usable_spills:
    print(" ", s)

print("\nExcluded spills (no genuine positive label):")
for s in excluded_spills:
    print(" ", s)


df = df[df["spill_id"].isin(usable_spills)].copy()

print(
    f"\nTraining/evaluation rows after filtering: "
    f"{len(df):,}"
)


# ============================================================
# FEATURES
# ============================================================

DROP_COLUMNS = [
    "spill_id",
    "vessel_id",
    "label",
]

feature_columns = [
    c for c in df.columns
    if c not in DROP_COLUMNS
]

X = df[feature_columns].copy()
y = df["label"].astype(int)


# XGBoost can handle NaNs, but make sure everything is numeric.
for col in X.columns:
    X[col] = pd.to_numeric(
        X[col],
        errors="coerce"
    )


print("\nFeature columns:")
for c in feature_columns:
    print(" ", c)


# ============================================================
# LEAVE-ONE-SPILL-OUT EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("LEAVE-ONE-SPILL-OUT EVALUATION")
print("=" * 70)

results = []

all_predictions = []


for test_spill in usable_spills:

    print("\n" + "-" * 70)
    print(f"TEST SPILL: {test_spill}")
    print("-" * 70)

    train_mask = df["spill_id"] != test_spill
    test_mask = df["spill_id"] == test_spill

    X_train = X.loc[train_mask]
    y_train = y.loc[train_mask]

    X_test = X.loc[test_mask]
    y_test = y.loc[test_mask]

    test_df = df.loc[test_mask].copy()

    print(f"Train rows: {len(X_train):,}")
    print(f"Test rows:  {len(X_test):,}")

    print(
        f"Train positives: {y_train.sum()}"
    )

    print(
        f"Test positives: {y_test.sum()}"
    )

    # --------------------------------------------------------
    # Class imbalance
    # --------------------------------------------------------

    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)

    if positives == 0:
        print("Skipping: no positive examples in training.")
        continue

    scale_pos_weight = negatives / positives

    print(
        f"scale_pos_weight: {scale_pos_weight:.2f}"
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
    )

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    test_df["prediction_probability"] = probabilities

    test_df = test_df.sort_values(
        "prediction_probability",
        ascending=False
    ).reset_index(drop=True)

    test_df["rank"] = (
        np.arange(len(test_df)) + 1
    )

    # --------------------------------------------------------
    # Ranking result
    # --------------------------------------------------------

    positive_rows = test_df[
        test_df["label"] == 1
    ]

    if len(positive_rows) > 0:

        positive_rank = int(
            positive_rows.iloc[0]["rank"]
        )

        positive_probability = float(
            positive_rows.iloc[0][
                "prediction_probability"
            ]
        )

    else:

        positive_rank = None
        positive_probability = None

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    if y_test.nunique() > 1:

        roc_auc = roc_auc_score(
            y_test,
            probabilities
        )

        average_precision = average_precision_score(
            y_test,
            probabilities
        )

    else:

        roc_auc = np.nan
        average_precision = np.nan

    # --------------------------------------------------------
    # Top-K hit
    # --------------------------------------------------------

    top1_hit = int(
        positive_rank is not None
        and positive_rank <= 1
    )

    top5_hit = int(
        positive_rank is not None
        and positive_rank <= 5
    )

    top10_hit = int(
        positive_rank is not None
        and positive_rank <= 10
    )

    top20_hit = int(
        positive_rank is not None
        and positive_rank <= 20
    )

    # --------------------------------------------------------
    # Print ranking
    # --------------------------------------------------------

    print("\nTop 10 candidates:")

    display_cols = [
        "rank",
        "vessel_id",
        "prediction_probability",
        "label",
        "min_distance_km",
        "mean_distance_km",
        "event_window_count",
        "loitering_events",
        "encounter_events",
        "gap_events",
    ]

    display_cols = [
        c for c in display_cols
        if c in test_df.columns
    ]

    print(
        test_df[display_cols]
        .head(10)
        .to_string(index=False)
    )

    print("\nGenuine vessel:")
    print(
        test_df[
            test_df["label"] == 1
        ][
            [
                "rank",
                "vessel_id",
                "prediction_probability",
            ]
        ].to_string(index=False)
    )

    print("\nMetrics:")
    print(f"  ROC-AUC:          {roc_auc}")
    print(f"  Average Precision:{average_precision}")
    print(f"  Positive rank:    {positive_rank}")
    print(f"  Top-1 hit:        {top1_hit}")
    print(f"  Top-5 hit:        {top5_hit}")
    print(f"  Top-10 hit:       {top10_hit}")
    print(f"  Top-20 hit:       {top20_hit}")

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    all_predictions.append(test_df)

    results.append({
        "spill_id": test_spill,
        "candidate_count": len(test_df),
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "positive_rank": positive_rank,
        "positive_probability": positive_probability,
        "top1": top1_hit,
        "top5": top5_hit,
        "top10": top10_hit,
        "top20": top20_hit,
    })


# ============================================================
# COMBINE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 70)
print("FINAL SPILL-LEVEL RESULTS")
print("=" * 70)

print(
    results_df.to_string(index=False)
)


# ============================================================
# AGGREGATE METRICS
# ============================================================

if len(results_df) > 0:

    print("\n" + "=" * 70)
    print("AGGREGATE PERFORMANCE")
    print("=" * 70)

    print(
        f"Mean ROC-AUC: "
        f"{results_df['roc_auc'].mean():.4f}"
    )

    print(
        f"Mean Average Precision: "
        f"{results_df['average_precision'].mean():.4f}"
    )

    print(
        f"Top-1 accuracy: "
        f"{results_df['top1'].mean():.4f}"
    )

    print(
        f"Top-5 hit rate: "
        f"{results_df['top5'].mean():.4f}"
    )

    print(
        f"Top-10 hit rate: "
        f"{results_df['top10'].mean():.4f}"
    )

    print(
        f"Top-20 hit rate: "
        f"{results_df['top20'].mean():.4f}"
    )


# ============================================================
# SAVE OUT-OF-FOLD PREDICTIONS
# ============================================================

if all_predictions:

    predictions_df = pd.concat(
        all_predictions,
        ignore_index=True
    )

    predictions_file = (
        BASE_DIR
        / "data"
        / "xgboost_oof_predictions.csv"
    )

    predictions_df.to_csv(
        predictions_file,
        index=False
    )

    print(
        f"\nSaved spill-level predictions to:\n"
        f"{predictions_file}"
    )


# ============================================================
# TRAIN FINAL MODEL ON ALL USABLE SPILLS
# ============================================================

print("\n" + "=" * 70)
print("TRAINING FINAL MODEL")
print("=" * 70)

positives = int(y.sum())
negatives = int(len(y) - positives)

scale_pos_weight = negatives / positives

final_model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1,
)

final_model.fit(
    X,
    y,
)

final_model.save_model(
    MODEL_FILE
)

print(
    f"\nFinal model saved to:\n{MODEL_FILE}"
)

print("\nDONE.")