import pandas as pd

from experiments.models import ClassificationPrediction, RegressionPrediction, TaskType

from .exceptions import ImportValidationError


class TaskStrategy:
    task = None
    prediction_model = None

    def convert(self, series, output_name, label):
        raise NotImplementedError

    def predictions(self, output):
        return self.prediction_model.objects.filter(output=output)

    def build_predictions(self, output, rows):
        return [
            self.prediction_model(output=output, sample_id=sample_id, true_label=true, predicted_label=pred)
            for sample_id, true, pred in rows
        ]


class ClassificationTask(TaskStrategy):
    task = TaskType.CLASSIF
    prediction_model = ClassificationPrediction

    def convert(self, series, output_name, label):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().all() and (numeric % 1 == 0).all():
            return numeric.astype("int64").astype(str)
        return series.astype(str).str.strip()


class RegressionTask(TaskStrategy):
    task = TaskType.REGR
    prediction_model = RegressionPrediction

    def convert(self, series, output_name, label):
        numbers = pd.to_numeric(series, errors="coerce")
        invalid = numbers.isna()
        if invalid.any():
            lines = ", ".join(str(i + 2) for i in series.index[invalid.to_numpy()][:5])
            raise ImportValidationError([
                f"A saída '{output_name}' foi marcada como regressão, mas o {label} "
                f"tem valores que não são números (linhas {lines})."
            ])
        return numbers


TASKS = {strategy.task: strategy for strategy in (ClassificationTask(), RegressionTask())}


def get_task(task):
    return TASKS[TaskType(task)]
