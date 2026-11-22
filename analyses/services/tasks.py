from experiments.models import TaskType

from .charts import confusion_matrix_chart, true_vs_predicted_chart
from .metrics import classification_metrics, load_predictions, regression_metrics


class AnalysisStrategy:
    task = None
    template_name = None
    ranking_metrics = {}
    lower_is_better = set()

    def compute_metrics(self, df):
        raise NotImplementedError

    def build_chart(self, df):
        raise NotImplementedError

    def find_worst(self, df, n):
        raise NotImplementedError

    def metrics_from(self, df):
        metrics = self.compute_metrics(df)
        metrics["n_samples"] = len(df)
        return metrics

    def output_metrics(self, output):
        df = load_predictions(output)
        return None if df.empty else self.metrics_from(df)

    def analyze(self, output, n_errors=10):
        df = load_predictions(output)
        if df.empty:
            return None
        return {
            "metrics": self.metrics_from(df),
            "chart": self.build_chart(df),
            "worst_errors": self.find_worst(df, n_errors),
            "template_name": self.template_name,
        }


class ClassificationAnalysis(AnalysisStrategy):
    task = TaskType.CLASSIF
    template_name = "analyses/partials/test_classification.html"
    ranking_metrics = {
        "accuracy": "Acurácia",
        "f1": "F1 (macro)",
        "precision": "Precisão (macro)",
        "recall": "Recall (macro)",
    }

    def compute_metrics(self, df):
        return classification_metrics(df["true_label"], df["predicted_label"])

    def build_chart(self, df):
        return confusion_matrix_chart(df)

    def find_worst(self, df, n):
        wrong = df[df["true_label"] != df["predicted_label"]]
        return wrong.head(n).to_dict("records")


class RegressionAnalysis(AnalysisStrategy):
    task = TaskType.REGR
    template_name = "analyses/partials/test_regression.html"
    ranking_metrics = {
        "mae": "MAE",
        "rmse": "RMSE",
        "r2": "R²",
        "mre": "MRE",
    }
    lower_is_better = {"mae", "rmse", "mre"}

    def compute_metrics(self, df):
        return regression_metrics(df["true_label"], df["predicted_label"])

    def build_chart(self, df):
        return true_vs_predicted_chart(df)

    def find_worst(self, df, n):
        df = df.assign(error=(df["predicted_label"] - df["true_label"]).abs())
        return df.sort_values("error", ascending=False).head(n).to_dict("records")


ANALYSES = {strategy.task: strategy for strategy in (ClassificationAnalysis(), RegressionAnalysis())}


def get_analysis(task):
    return ANALYSES[TaskType(task)]
