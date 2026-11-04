import pandas as pd

TRAIN_FIELDS = {
    "step": "Passo (época ou iteração)",
    "epoch": "Época",
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


def read_table(file):
    name = getattr(file, "name", str(file)).lower()
    try:
        if name.endswith(['.xlsx', '.xls']):
            df = pd.read_excel(name)
        else:
            df = pd.read_csv(name)
    except Exception as e:
        raise ImportError(['Não foi possível ler o arquivo. Ele precisa ser um csv ou xlsx/xls'])

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
