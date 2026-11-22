import shutil
import tempfile

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import ClassificationPrediction, Experiment, Project, RegressionPrediction, StepMetric, TaskType
from .services.exceptions import ImportValidationError
from .services.parsing import describe_outputs, detect_task, find_outputs, normalize_test, prepare_outputs
from .services.tasks import ClassificationTask, RegressionTask, get_task

MEDIA_ROOT = tempfile.mkdtemp()


def create_user(username):
    return get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="senha-forte-123"
    )


class TaskStrategyTests(SimpleTestCase):
    def test_each_task_has_its_strategy(self):
        self.assertIsInstance(get_task(TaskType.CLASSIF), ClassificationTask)
        self.assertIsInstance(get_task(TaskType.REGR), RegressionTask)

    def test_each_strategy_saves_in_its_own_table(self):
        self.assertIs(get_task(TaskType.CLASSIF).prediction_model, ClassificationPrediction)
        self.assertIs(get_task(TaskType.REGR).prediction_model, RegressionPrediction)

    def test_classification_turns_integer_labels_into_text_without_decimals(self):
        labels = get_task(TaskType.CLASSIF).convert(pd.Series([1.0, 2.0]), "classe", "valor real")
        self.assertEqual(labels.tolist(), ["1", "2"])

    def test_classification_strips_spaces_from_labels(self):
        labels = get_task(TaskType.CLASSIF).convert(pd.Series([" gato ", "cão"]), "classe", "valor real")
        self.assertEqual(labels.tolist(), ["gato", "cão"])

    def test_regression_converts_text_numbers(self):
        numbers = get_task(TaskType.REGR).convert(pd.Series(["1.5", "2"]), "idade", "valor real")
        self.assertEqual(numbers.tolist(), [1.5, 2.0])

    def test_regression_rejects_text_and_reports_the_spreadsheet_line(self):
        series = pd.Series(["1.5", "abc", "2"])
        with self.assertRaises(ImportValidationError) as context:
            get_task(TaskType.REGR).convert(series, "idade", "valor real")
        self.assertIn("linhas 3", context.exception.messages[0])


class ParsingTests(SimpleTestCase):
    def test_detect_task_suggestions(self):
        self.assertEqual(detect_task(pd.Series(["gato", "cão"])), TaskType.CLASSIF)
        self.assertEqual(detect_task(pd.Series([0, 1, 2])), TaskType.CLASSIF)
        self.assertEqual(detect_task(pd.Series([1.5, 2.7])), TaskType.REGR)
        self.assertEqual(detect_task(pd.Series(range(30))), TaskType.REGR)

    def test_find_outputs_pairs_true_and_pred_columns(self):
        df = pd.DataFrame(columns=["sample_id", "true_doenca", "pred_doenca", "true_idade", "pred_idade", "true_label"])
        self.assertEqual([name for name, _, _ in find_outputs(df)], ["doenca", "idade"])

    def test_normalize_test_turns_the_single_output_format_into_principal(self):
        df = pd.DataFrame({"id": ["a"], "real": ["x"], "predito": ["x"]})
        normalized = normalize_test(df, {"sample_id": "id", "true_label": "real", "predicted_label": "predito"})
        self.assertEqual([name for name, _, _ in find_outputs(normalized)], ["principal"])

    def test_describe_outputs_suggests_tasks_and_ignores_empty_outputs(self):
        df = pd.DataFrame({
            "sample_id": ["a", "b"],
            "true_doenca": ["ferrugem", "mancha"],
            "pred_doenca": ["ferrugem", "ferrugem"],
            "true_idade": [30.5, 40.0],
            "pred_idade": [31.2, 38.9],
            "true_vazia": [None, None],
            "pred_vazia": [None, None],
        })
        outputs = describe_outputs(df)
        self.assertEqual(
            [(o["name"], o["suggested"]) for o in outputs],
            [("doenca", TaskType.CLASSIF.value), ("idade", TaskType.REGR.value)],
        )

    def test_describe_outputs_requires_sample_id(self):
        df = pd.DataFrame({"id": ["a"], "true_doenca": ["x"], "pred_doenca": ["x"]})
        with self.assertRaises(ImportValidationError):
            describe_outputs(df)

    def test_prepare_outputs_skips_empty_cells_only_in_that_output(self):
        df = pd.DataFrame({
            "sample_id": ["a", "b"],
            "true_doenca": ["ferrugem", "mancha"],
            "pred_doenca": ["ferrugem", "ferrugem"],
            "true_idade": [30.5, None],
            "pred_idade": [31.2, None],
        })
        outputs = prepare_outputs(df, {"doenca": TaskType.CLASSIF, "idade": TaskType.REGR})
        sizes = {output["name"]: len(output["rows"]) for output in outputs}
        self.assertEqual(sizes, {"doenca": 2, "idade": 1})


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ImportFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = create_user("ana")
        self.client.force_login(self.user)
        project = Project.objects.create(name="Folhas", analyst=self.user)
        self.experiment = Experiment.objects.create(project=project, name="resnet")

    def url(self, name):
        return reverse(name, args=[self.experiment.pk])

    def upload(self, content, kind):
        file = SimpleUploadedFile("planilha.csv", content.encode(), content_type="text/csv")
        return self.client.post(self.url("experiment_import"), {"kind": kind, "file": file})

    def test_training_spreadsheet_is_saved_directly(self):
        csv = "epoch,train_loss,val_loss,train_accuracy,val_accuracy\n1,0.9,0.8,0.5,0.6\n2,0.5,0.6,0.7,0.65\n"
        response = self.upload(csv, "train")
        self.assertRedirects(response, self.url("experiment_import"))
        self.assertEqual(self.experiment.steps.count(), 2)
        self.assertEqual(StepMetric.objects.filter(step__experiment=self.experiment).count(), 4)

    def test_test_spreadsheet_waits_for_confirmation_and_uses_the_chosen_tasks(self):
        csv = (
            "sample_id,true_doenca,pred_doenca,true_idade,pred_idade\n"
            "a,ferrugem,ferrugem,30.5,31.0\n"
            "b,mancha,ferrugem,40.0,38.2\n"
        )
        response = self.upload(csv, "test")
        self.assertRedirects(response, self.url("experiment_import_tasks"))
        self.assertFalse(self.experiment.outputs.exists())

        response = self.client.post(
            self.url("experiment_import_tasks"),
            {"task_0": TaskType.CLASSIF, "task_1": TaskType.REGR},
        )
        self.assertRedirects(response, self.url("experiment_results"))
        tasks = {output.name: output.task for output in self.experiment.outputs.all()}
        self.assertEqual(tasks, {"doenca": TaskType.CLASSIF, "idade": TaskType.REGR})
        self.assertEqual(RegressionPrediction.objects.filter(output__name="idade").count(), 2)

    def test_text_marked_as_regression_is_rejected_on_the_confirmation_screen(self):
        csv = "sample_id,true_label,predicted_label\na,gato,gato\nb,cão,gato\n"
        self.upload(csv, "test")
        response = self.client.post(self.url("experiment_import_tasks"), {"task_0": TaskType.REGR})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "foi marcada como regressão")
        self.assertFalse(self.experiment.outputs.exists())


class AccessAndSearchTests(TestCase):
    def setUp(self):
        self.user = create_user("ana")
        self.client.force_login(self.user)

    def test_user_cannot_open_another_users_project(self):
        other_project = Project.objects.create(name="Privado", analyst=create_user("bia"))
        response = self.client.get(reverse("experiment_list", args=[other_project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_project_search_filters_by_name(self):
        Project.objects.create(name="Folhas de café", analyst=self.user)
        Project.objects.create(name="Raio-X", analyst=self.user)
        response = self.client.get(reverse("project_list"), {"q": "folhas"})
        self.assertContains(response, "Folhas de café")
        self.assertNotContains(response, "Raio-X")
