import pandas as pd
import plotly.graph_objects as go

from experiments.models import StepMetric, StepUnit, TaskType

from .metrics import confusion_matrix, load_predictions


def _to_html(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=50, r=20, t=50, b=50),
        legend=dict(orientation="h", y=-0.2),
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def _step_label(experiment):
    return "Iteração" if experiment.step_unit == StepUnit.ITER else "Época"


def training_metric_names(experiment):
    names = (
        StepMetric.objects.filter(step__experiment=experiment)
        .values_list("metric", flat=True)
        .distinct()
    )
    return ["loss"] + sorted(names)


def _training_series(experiment, metric):
    if metric == "loss":
        rows = experiment.steps.values("step", "train_loss", "val_loss")
        df = pd.DataFrame(list(rows), columns=["step", "train_loss", "val_loss"])
        df = df.rename(columns={"train_loss": "train", "val_loss": "val"})
    else:
        rows = StepMetric.objects.filter(step__experiment=experiment, metric=metric).values(
            "step__step", "split", "value"
        )
        df = pd.DataFrame(list(rows), columns=["step__step", "split", "value"])
        if df.empty:
            return df

        df = df.pivot_table(index="step__step", columns="split", values="value").reset_index()
        df = df.rename(columns={"step__step": "step"})

    for split in ("train", "val"):
        if split not in df.columns:
            df[split] = float("nan")
    return df.sort_values("step")


def training_curve(experiment, metric="loss"):
    df = _training_series(experiment, metric)
    if df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["step"], y=df["train"], mode="lines", name="Treino"))
    if df["val"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["step"], y=df["val"], mode="lines+markers", name="Validação",
            connectgaps=True,
        ))
    fig.update_layout(title=metric, xaxis_title=_step_label(experiment), yaxis_title=metric)
    return _to_html(fig)


def compare_training_curves(experiments, metric="loss", split="val"):
    fig = go.Figure()
    for experiment in experiments:
        df = _training_series(experiment, metric)
        if df.empty or df[split].isna().all():
            continue
        fig.add_trace(go.Scatter(
            x=df["step"], y=df[split], mode="lines", name=experiment.name, connectgaps=True,
        ))

    if not fig.data:
        return None
    split_name = "validação" if split == "val" else "treino"
    fig.update_layout(title=f"{metric} ({split_name})", xaxis_title="Passo", yaxis_title=metric)
    return _to_html(fig)


def confusion_matrix_chart(experiment):
    if experiment.task != TaskType.CLASSIF:
        return None
    df = load_predictions(experiment)
    if df.empty:
        return None

    labels, matrix = confusion_matrix(df["true_label"], df["predicted_label"])
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        text=matrix,
        texttemplate="%{text}",
        colorscale="Blues",
        showscale=False,
    ))
    fig.update_layout(title="Matriz de confusão", xaxis_title="Predito", yaxis_title="Real")
    fig.update_yaxes(autorange="reversed")
    return _to_html(fig)


def true_vs_predicted_chart(experiment):
    if experiment.task != TaskType.REGR:
        return None
    df = load_predictions(experiment)
    if df.empty:
        return None

    low = min(df["true_label"].min(), df["predicted_label"].min())
    high = max(df["true_label"].max(), df["predicted_label"].max())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["true_label"], y=df["predicted_label"], mode="markers", name="Amostras",
        text=df["sample_id"],
        marker=dict(size=7, opacity=0.7),
    ))
    fig.add_trace(go.Scatter(
        x=[low, high], y=[low, high], mode="lines", name="Ideal (y = x)",
        line=dict(dash="dash", color="gray"),
    ))
    fig.update_layout(title="Real x predito", xaxis_title="Valor real", yaxis_title="Valor predito")
    return _to_html(fig)