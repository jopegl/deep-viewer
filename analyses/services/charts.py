import json
import math

import pandas as pd
import plotly.graph_objects as go

from experiments.models import StepMetric, StepUnit, TaskType

from .metrics import confusion_matrix, load_predictions


ANIMATE_JS = """
var gd = document.getElementById('{plot_id}');
var targets = __TARGETS__;
var data = [];
var traces = [];
targets.forEach(function (y, i) {
  if (y) {
    data.push({y: y});
    traces.push(i);
  }
});
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  Plotly.restyle(gd, {y: data.map(function (d) { return d.y; })}, traces);
} else {
  Plotly.animate(gd, {data: data, traces: traces}, {
    transition: {duration: 900, easing: 'cubic-in-out'},
    frame: {duration: 900, redraw: false}
  });
}
"""


def _clean(values):
    cleaned = []
    for value in values:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            cleaned.append(None)
        else:
            cleaned.append(float(value))
    return cleaned


def _prepare_animation(fig):
    targets = []
    known = []
    for trace in fig.data:
        if trace.y is None:
            targets.append(None)
            continue
        y = _clean(list(trace.y))
        targets.append(y)
        known.extend(v for v in y if v is not None)

    if not known:
        return None

    low, high = min(known), max(known)
    pad = (high - low) * 0.06 or 1
    floor = low - pad
    fig.update_yaxes(range=[floor, high + pad], autorange=False)

    for trace, y in zip(fig.data, targets):
        if y is not None:
            trace.y = [None if v is None else floor for v in y]

    fig.update_traces(line_simplify=False, selector=dict(type="scatter"))

    return ANIMATE_JS.replace("__TARGETS__", json.dumps(targets))


def _to_html(fig, animate=False):
    fig.update_layout(
        template="plotly_dark",
        title=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, system-ui, sans-serif", size=13, color="#c9d6cf"),
        colorway=["#4cc38a", "#8aa4c8", "#e3b565", "#c792ea", "#e5736b"],
        margin=dict(l=50, r=20, t=10, b=50),
        legend=dict(orientation="h", y=-0.2),
        hoverlabel=dict(bgcolor="#1c2823", bordercolor="#35473f", font_color="#e6eee9"),
    )
    fig.update_xaxes(gridcolor="#24322c", zerolinecolor="#24322c", linecolor="#35473f")
    fig.update_yaxes(gridcolor="#24322c", zerolinecolor="#24322c", linecolor="#35473f")

    post_script = _prepare_animation(fig) if animate else None
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"displaylogo": False, "responsive": True},
        post_script=post_script,
    )


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
    return _to_html(fig, animate=True)


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
    return _to_html(fig, animate=True)


def confusion_matrix_chart(output):
    if output.task != TaskType.CLASSIF:
        return None
    df = load_predictions(output)
    if df.empty:
        return None

    labels, matrix = confusion_matrix(df["true_label"], df["predicted_label"])
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        text=matrix,
        texttemplate="%{text}",
        colorscale=[[0, "#15201b"], [1, "#4cc38a"]],
        showscale=False,
    ))
    fig.update_layout(title="Matriz de confusão", xaxis_title="Predito", yaxis_title="Real")
    fig.update_yaxes(autorange="reversed")
    return _to_html(fig)


def true_vs_predicted_chart(output):
    if output.task != TaskType.REGR:
        return None
    df = load_predictions(output)
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
        line=dict(dash="dash", color="#66796f"),
    ))
    fig.update_layout(title="Real x predito", xaxis_title="Valor real", yaxis_title="Valor predito")
    return _to_html(fig, animate=True)