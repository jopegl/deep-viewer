from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

WIDTH = 300
HEIGHT = 84


def _points(values, low, high):
    span = (high - low) or 1
    last = len(values) - 1
    points = []
    for i, value in enumerate(values):
        if value is None:
            continue
        x = i / last * WIDTH
        y = HEIGHT - (value - low) / span * HEIGHT
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


@register.simple_tag
def loss_sparkline(experiment):
    rows = list(experiment.steps.order_by("step").values_list("train_loss", "val_loss"))
    if len(rows) < 2:
        return ""

    train = [row[0] for row in rows]
    val = [row[1] for row in rows]
    known = [v for v in train + val if v is not None]
    low, high = min(known), max(known)

    lines = []
    if sum(v is not None for v in val) >= 2:
        lines.append(format_html(
            '<polyline class="spark-val" points="{}" fill="none" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />',
            _points(val, low, high),
        ))
    lines.append(format_html(
        '<polyline class="spark-train" points="{}" fill="none" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />',
        _points(train, low, high),
    ))

    return format_html(
        '<svg class="spark" viewBox="0 0 {} {}" preserveAspectRatio="none" aria-hidden="true">{}</svg>',
        WIDTH, HEIGHT, mark_safe("".join(lines)),
    )