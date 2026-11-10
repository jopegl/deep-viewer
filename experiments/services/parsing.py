import pandas as pd

from experiments.services.exceptions import ImportValidationError
from experiments.models import TaskType

TRAIN_FIELDS = {
    "step": "Passo (época ou iteração)",
    "train_loss": "Loss de treino",
    "val_loss": "Loss de validação",
    "learning_rate": "Learning rate",
}
TEST_FIELDS = {
    "sample_id": "ID da amostra",
    "true_label": "Valor real",
    "predicted_label": "Valor predito",
}

TRAIN_OPTIONAL = {"val_loss", "learning_rate"}

METRIC_PREFIXES = {"train_": "train", "val_": "val"}


def read_table(file):
    name = getattr(file, "name", str(file)).lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file, sep=None, engine="python", encoding="utf-8-sig")
    except Exception as e:
        raise ImportValidationError(["Não foi possível ler o arquivo. Ele precisa ser um csv ou xlsx/xls"]) from e

    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        raise ImportValidationError(["O arquivo não tem nenhuma linha de dados."])
    return df


def expected_columns_train(step_unit):
    return {
        "step": "iteration" if step_unit == "iter" else "epoch",
        "train_loss": "train_loss",
        "val_loss": "val_loss",
        "learning_rate": "learning_rate",
    }


def expected_columns_test():
    return {field: field for field in TEST_FIELDS}


def _match_columns(columns, expected, optional):
    by_lower = {c.lower(): c for c in columns}
    mapping, missing = {}, []
    for field, name in expected.items():
        col = by_lower.get(name)
        mapping[field] = col
        if col is None and field not in optional:
            missing.append(name)
    return mapping, missing


def match_train_columns(columns, step_unit):
    return _match_columns(columns, expected_columns_train(step_unit), TRAIN_OPTIONAL)


def match_test_columns(columns):
    return _match_columns(columns, expected_columns_test(), optional=set())


def find_metric_columns(columns, mapping):
    used = mapping.values()
    return [c for c in columns if c not in used and c.startswith(("train_", "val_"))]


def prepare_training(df, mapping, metric_columns=()):
    steps = pd.DataFrame()
    for field in ["step", "train_loss", "val_loss", "learning_rate"]:
        col = mapping.get(field)
        steps[field] = df[col] if col else None

    metrics = []
    for col in metric_columns:
        prefix = "train_" if col.startswith("train_") else "val_"
        name = col[len(prefix):]
        for step, value in zip(df[mapping["step"]], df[col]):
            if pd.notna(value):
                metrics.append({
                    "step": int(step),
                    "metric": name,
                    "split": METRIC_PREFIXES[prefix],
                    "value": float(value),
                })
    return steps, metrics


def prepare_test(df, mapping, is_regression):
    data = pd.DataFrame({
        "sample_id": df[mapping["sample_id"]].astype(str),
        "true_label": df[mapping["true_label"]],
        "predicted_label": df[mapping["predicted_label"]],
    })

    if is_regression:
        bad_columns = []
        bad_lines = set()
        for field, label in (("true_label", "Valor real"), ("predicted_label", "Valor predito")):
            numbers = pd.to_numeric(data[field], errors="coerce")
            invalid = numbers.isna() & data[field].notna()
            if invalid.any():
                bad_columns.append(label)
                bad_lines.update(invalid[invalid].index)
            data[field] = numbers

        if bad_columns:
            lines = ", ".join(str(i + 2) for i in sorted(bad_lines)[:5])
            raise ImportValidationError([
                f"{' e '.join(bad_columns)} têm valores que não são números (linhas {lines}). "
                "Este experimento é de regressão: a planilha é de classificação?"
            ])
    else:
        data["true_label"] = data["true_label"].astype(str)
        data["predicted_label"] = data["predicted_label"].astype(str)
    return data

def find_outputs(df):
    columns = {c.lower(): c for c in df.columns}
    outputs = []
    for low, original in columns.items():
        if low.startswith("true_") and low != "true_label":
            name = low[len("true_"):]
            pred = columns.get(f"pred_{name}")
            if pred:
                outputs.append((name, original, pred))
    return outputs


def detect_task(values):
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any():
        return TaskType.CLASSIF
    if (numeric % 1 == 0).all() and numeric.nunique() <= 20:
        return TaskType.CLASSIF
    return TaskType.REGR


def _labels(series):
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all() and (numeric % 1 == 0).all():
        return numeric.astype("int64").astype(str)
    return series.astype(str).str.strip()


def prepare_outputs(df):
    columns = {c.lower(): c for c in df.columns}
    if "sample_id" not in columns:
        raise ImportValidationError(["A planilha precisa da coluna sample_id."])

    outputs = []
    for name, true_col, pred_col in find_outputs(df):
        filled = df[true_col].notna() & df[pred_col].notna()
        part = df[filled]
        sample_ids = part[columns["sample_id"]].astype(str).str.strip()
        task = detect_task(pd.concat([part[true_col], part[pred_col]]))
        if task == TaskType.REGR:
            true_values = pd.to_numeric(part[true_col])
            pred_values = pd.to_numeric(part[pred_col])
        else:
            true_values = _labels(part[true_col])
            pred_values = _labels(part[pred_col])
        outputs.append({
            "name": name,
            "task": task,
            "rows": list(zip(sample_ids, true_values, pred_values)),
        })
    return outputs