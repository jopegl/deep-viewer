import numpy as np
import pandas as pd

from experiments.models import TaskType


def load_predictions(output):
    queryset = output.regr_preds if output.task == TaskType.REGR else output.classi_preds
    rows = queryset.values("sample_id", "true_label", "predicted_label")
    return pd.DataFrame(list(rows), columns=["sample_id", "true_label", "predicted_label"])




def classification_metrics(y_true, y_pred):
    y_true = pd.Series(y_true).astype(str).reset_index(drop=True)
    y_pred = pd.Series(y_pred).astype(str).reset_index(drop=True)
    labels = sorted(set(y_true) | set(y_pred))

    per_class = []
    for label in labels:
        tp = int(((y_true == label) & (y_pred == label)).sum())
        fp = int(((y_true != label) & (y_pred == label)).sum())
        fn = int(((y_true == label) & (y_pred != label)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({
            "label": label,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int((y_true == label).sum()),
        })

    return {
        "accuracy": float((y_true == y_pred).mean()),
        "precision": float(np.mean([c["precision"] for c in per_class])),
        "recall": float(np.mean([c["recall"] for c in per_class])),
        "f1": float(np.mean([c["f1"] for c in per_class])),
        "per_class": per_class,
    }


def confusion_matrix(y_true, y_pred):
    y_true = pd.Series(y_true).astype(str).reset_index(drop=True)
    y_pred = pd.Series(y_pred).astype(str).reset_index(drop=True)
    labels = sorted(set(y_true) | set(y_pred))
    table = pd.crosstab(y_true, y_pred).reindex(index=labels, columns=labels, fill_value=0)
    return labels, table.values.tolist()


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    errors = y_pred - y_true

    ss_res = float(np.sum(errors ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot == 0:
        r2 = 1.0 if ss_res == 0 else 0.0
    else:
        r2 = 1 - ss_res / ss_tot

    nonzero = y_true != 0
    if nonzero.any():
        mre = float(np.mean(np.abs(errors[nonzero]) / np.abs(y_true[nonzero])))
    else:
        mre = None

    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        "r2": r2,
        "mre": mre,
    }


def output_metrics(output):
    df = load_predictions(output)
    if df.empty:
        return None

    if output.task == TaskType.REGR:
        metrics = regression_metrics(df["true_label"], df["predicted_label"])
    else:
        metrics = classification_metrics(df["true_label"], df["predicted_label"])
    metrics["n_samples"] = len(df)
    return metrics


def worst_errors(output, n=10):
    df = load_predictions(output)
    if df.empty:
        return []

    if output.task == TaskType.REGR:
        df["error"] = (df["predicted_label"] - df["true_label"]).abs()
        df = df.sort_values("error", ascending=False)
    else:
        df = df[df["true_label"] != df["predicted_label"]]

    return df.head(n).to_dict("records")