import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from sklearn import metrics as sk

from experiments.models import Experiment, Output, Project, TaskType
from experiments.services.tasks import get_task

from .services.metrics import classification_metrics, confusion_matrix, regression_metrics
from .services.ranking import rank_experiments
from .services.tasks import ClassificationAnalysis, RegressionAnalysis, get_analysis


class ClassificationMetricsTests(SimpleTestCase):
    y_true = ["gato", "gato", "cachorro", "cachorro", "passaro", "passaro", "gato"]
    y_pred = ["gato", "cachorro", "cachorro", "cachorro", "passaro", "gato", "gato"]

    def test_accuracy_hand_calculated(self):
        result = classification_metrics(self.y_true, self.y_pred)
        self.assertAlmostEqual(result["accuracy"], 5 / 7)

    def test_macro_metrics_match_sklearn(self):
        result = classification_metrics(self.y_true, self.y_pred)
        expected = {
            "precision": sk.precision_score,
            "recall": sk.recall_score,
            "f1": sk.f1_score,
        }
        for name, function in expected.items():
            with self.subTest(metric=name):
                value = function(self.y_true, self.y_pred, average="macro", zero_division=0)
                self.assertAlmostEqual(result[name], value)

    def test_class_never_predicted_has_zero_precision(self):
        result = classification_metrics(["a", "b", "b"], ["b", "b", "b"])
        per_class = {row["label"]: row for row in result["per_class"]}
        self.assertEqual(per_class["a"]["precision"], 0.0)
        self.assertEqual(per_class["a"]["support"], 1)

    def test_confusion_matrix_matches_sklearn(self):
        labels, matrix = confusion_matrix(self.y_true, self.y_pred)
        expected = sk.confusion_matrix(self.y_true, self.y_pred, labels=labels)
        self.assertEqual(matrix, expected.tolist())


class RegressionMetricsTests(SimpleTestCase):
    y_true = [3.0, -0.5, 2.0, 7.0, 4.0]
    y_pred = [2.5, 0.0, 2.0, 8.0, 3.0]

    def test_mae_hand_calculated(self):
        result = regression_metrics(self.y_true, self.y_pred)
        self.assertAlmostEqual(result["mae"], 0.6)

    def test_metrics_match_sklearn(self):
        result = regression_metrics(self.y_true, self.y_pred)
        self.assertAlmostEqual(result["mae"], sk.mean_absolute_error(self.y_true, self.y_pred))
        self.assertAlmostEqual(result["rmse"], np.sqrt(sk.mean_squared_error(self.y_true, self.y_pred)))
        self.assertAlmostEqual(result["r2"], sk.r2_score(self.y_true, self.y_pred))

    def test_mre_ignores_zero_true_values(self):
        result = regression_metrics([0.0, 2.0, 4.0], [1.0, 3.0, 2.0])
        self.assertAlmostEqual(result["mre"], 0.5)

    def test_mre_is_none_when_every_true_value_is_zero(self):
        result = regression_metrics([0.0, 0.0], [1.0, 2.0])
        self.assertIsNone(result["mre"])

    def test_perfect_prediction(self):
        result = regression_metrics([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual(result["mae"], 0.0)
        self.assertEqual(result["r2"], 1.0)


class AnalysisStrategyTests(SimpleTestCase):
    def test_each_task_has_its_strategy(self):
        self.assertIsInstance(get_analysis(TaskType.CLASSIF), ClassificationAnalysis)
        self.assertIsInstance(get_analysis(TaskType.REGR), RegressionAnalysis)

    def test_classification_worst_errors_are_the_misclassified_samples(self):
        df = pd.DataFrame({
            "sample_id": ["a", "b", "c"],
            "true_label": ["x", "y", "x"],
            "predicted_label": ["x", "x", "y"],
        })
        worst = ClassificationAnalysis().find_worst(df, 10)
        self.assertEqual([row["sample_id"] for row in worst], ["b", "c"])

    def test_regression_worst_errors_are_sorted_by_absolute_error(self):
        df = pd.DataFrame({
            "sample_id": ["a", "b", "c"],
            "true_label": [1.0, 5.0, 10.0],
            "predicted_label": [1.5, 9.0, 10.0],
        })
        worst = RegressionAnalysis().find_worst(df, 2)
        self.assertEqual([row["sample_id"] for row in worst], ["b", "a"])

    def test_only_regression_errors_are_ranked_from_lowest(self):
        self.assertEqual(ClassificationAnalysis.lower_is_better, set())
        self.assertIn("mae", RegressionAnalysis.lower_is_better)


class AnalysisWithDatabaseTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="ana", email="ana@example.com", password="senha-forte-123"
        )
        self.project = Project.objects.create(name="Folhas", analyst=user)

    def create_output(self, experiment_name, task, rows):
        experiment = Experiment.objects.create(project=self.project, name=experiment_name)
        output = Output.objects.create(experiment=experiment, name="principal", task=task)
        strategy = get_task(task)
        strategy.prediction_model.objects.bulk_create(strategy.build_predictions(output, rows))
        return output

    def test_analyze_returns_metrics_chart_and_template(self):
        output = self.create_output("resnet", TaskType.CLASSIF, [("a", "x", "x"), ("b", "x", "y")])
        result = get_analysis(output.task).analyze(output)
        self.assertEqual(result["metrics"]["n_samples"], 2)
        self.assertAlmostEqual(result["metrics"]["accuracy"], 0.5)
        self.assertEqual(result["template_name"], "analyses/partials/test_classification.html")
        self.assertIn("plotly", result["chart"].lower())

    def test_analyze_without_predictions_returns_none(self):
        output = self.create_output("vazio", TaskType.REGR, [])
        self.assertIsNone(get_analysis(output.task).analyze(output))

    def test_regression_ranking_puts_the_lowest_mae_first(self):
        self.create_output("pior", TaskType.REGR, [("a", 1.0, 3.0), ("b", 2.0, 4.0)])
        self.create_output("melhor", TaskType.REGR, [("a", 1.0, 1.1), ("b", 2.0, 2.1)])
        rows = rank_experiments(self.project, TaskType.REGR, "mae")
        self.assertEqual([row["experiment"].name for row in rows], ["melhor", "pior"])
        self.assertEqual(rows[0]["position"], 1)

    def test_classification_ranking_puts_the_highest_accuracy_first(self):
        self.create_output("pior", TaskType.CLASSIF, [("a", "x", "y"), ("b", "x", "x")])
        self.create_output("melhor", TaskType.CLASSIF, [("a", "x", "x"), ("b", "x", "x")])
        rows = rank_experiments(self.project, TaskType.CLASSIF, "accuracy")
        self.assertEqual([row["experiment"].name for row in rows], ["melhor", "pior"])
