import pandas as pd

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

TRAIN_OPTIONAL = {"epoch", "val_loss", "learning_rate"}

METRIC_PREFIXES = {"train_": "train", "val_": "val"}




def read_table(file):
    name = getattr(file, "name", str(file)).lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file, sep=None, engine="python", encoding="utf-8-sig")
    except Exception as e:
        raise Exception(["Não foi possível ler o arquivo. Ele precisa ser um csv ou xlsx/xls"]) from e

    df.columns = [str(c).strip() for c in df.columns]
    return df

def expected_columns_train(step_unit):
    names = {
        "step": "iteration" if step_unit == "iter" else "epoch",
        "train_loss": "train_loss",
        "val_loss": "val_loss",
        "learning_rate": "learning_rate",
    }

    return names

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
    if not is_regression:
        data["true_label"] = data["true_label"].astype(str)
        data["predicted_label"] = data["predicted_label"].astype(str)
    return data

