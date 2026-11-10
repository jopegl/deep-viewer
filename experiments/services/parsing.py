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


def normalize_test(df, mapping):
    return pd.DataFrame({
        "sample_id": df[mapping["sample_id"]],
        "true_principal": df[mapping["true_label"]],
        "pred_principal": df[mapping["predicted_label"]],
    })


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


def _sample_column(df):
    columns = {c.lower(): c for c in df.columns}
    if "sample_id" not in columns:
        raise ImportValidationError(["A planilha precisa da coluna sample_id."])
    return columns["sample_id"]


def describe_outputs(df):
    _sample_column(df)
    outputs = []
    for name, true_col, pred_col in find_outputs(df):
        values = pd.concat([df[true_col], df[pred_col]]).dropna()
        if values.empty:
            continue
        outputs.append({
            "name": name,
            "suggested": detect_task(values).value,
            "examples": values.astype(str).str.strip().drop_duplicates().head(5).tolist(),
        })
    if not outputs:
        raise ImportValidationError(["Nenhuma saída da planilha tem valores preenchidos."])
    return outputs


def _labels(series):
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all() and (numeric % 1 == 0).all():
        return numeric.astype("int64").astype(str)
    return series.astype(str).str.strip()


def _numbers(part, column, output_name, label):
    numbers = pd.to_numeric(part[column], errors="coerce")
    invalid = numbers.isna()
    if invalid.any():
        lines = ", ".join(str(i + 2) for i in part.index[invalid.to_numpy()][:5])
        raise ImportValidationError([
            f"A saída '{output_name}' foi marcada como regressão, mas o {label} "
            f"tem valores que não são números (linhas {lines})."
        ])
    return numbers


def prepare_outputs(df, tasks):
    sample_col = _sample_column(df)
    outputs = []
    for name, true_col, pred_col in find_outputs(df):
        if name not in tasks:
            continue
        task = tasks[name]
        filled = df[true_col].notna() & df[pred_col].notna()
        part = df[filled]
        sample_ids = part[sample_col].astype(str).str.strip()
        if task == TaskType.REGR:
            true_values = _numbers(part, true_col, name, "valor real")
            pred_values = _numbers(part, pred_col, name, "valor predito")
        else:
            true_values = _labels(part[true_col])
            pred_values = _labels(part[pred_col])
        outputs.append({
            "name": name,
            "task": task,
            "rows": list(zip(sample_ids, true_values, pred_values)),
        })
    return outputs
