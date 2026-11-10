# Deep Viewer

A web application for recording and analyzing deep learning training experiments.

Researchers organize their studies into **projects**, register each training run as an **experiment**, and import two spreadsheets produced by their training code (PyTorch): the **training log** (loss and metrics per epoch or iteration) and the **test set results** (true and predicted value per sample, for one or more outputs of the network). From these, the system generates learning curves, test metrics and comparisons between experiments.

Developed for the **DCC061 – Software Engineering** course.

> **Status:** in development.

---

## Features

**Implemented**

- Landing page, sign-up, login and profile editing
- Institution search on sign-up and profile, using the [ROR](https://ror.org) registry
- Every page requires login; the admin panel is only available to staff users
- Projects and experiments (per epoch or per iteration), with creation and deletion
- Import of training and test spreadsheets (CSV or Excel)
- Automatic column recognition when the spreadsheet follows the naming convention
- Column mapping screen when the spreadsheet uses different names
- **Multi-output networks**: one test spreadsheet can hold several outputs (e.g. a disease class and an age), each with its own task and metrics
- Confirmation screen for the task of each output (classification or regression), with a suggestion detected from the values
- Re-import: uploading a spreadsheet again replaces the previous data
- Experiment dashboard:
  - training vs. validation curves for the loss and for every metric
  - output selector for multi-output experiments
  - classification: accuracy, precision, recall, F1, confusion matrix, per-class metrics and misclassified samples
  - regression: MAE, RMSE, R², MRE, true vs. predicted plot and largest errors
- Experiment cards with a loss preview curve

**Planned**

- Experiment ranking and comparison screen
- Detailed validation of the training spreadsheet, reporting the row of each error
- Support for decimal commas (spreadsheets exported by Excel in Portuguese)
- PDF report

---

## Tech stack

- Python 3.12
- Django 6.1
- pandas and openpyxl (spreadsheet reading)
- Plotly (charts)
- scikit-learn (used in the tests to check the metrics)
- SQLite

---

## Getting started

The commands below are for Linux and macOS. On Windows, only the virtual environment activation differs (see step 2).

**1. Clone the repository**

```bash
git clone <repository-url>
cd deep-viewer
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\Activate.ps1       # Windows (PowerShell)
```

**3. Install the dependencies**

```bash
pip install -r requirements.txt
```

**4. Create the database**

```bash
python manage.py migrate
```

**5. (Optional) Create an admin user**

```bash
python manage.py createsuperuser
```

**6. Start the server**

```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser. Admin users can reach the admin panel at http://127.0.0.1:8000/admin/ after logging in.

---

## Usage

1. Create an account and log in.
2. Create a **project**.
3. Inside the project, create an **experiment**, choosing its step unit (epoch or iteration).
4. Click **Importar planilhas**, choose the spreadsheet type (train or test), select the file and click **Importar**.
5. If the column names follow the convention below, the system recognizes them on its own. Otherwise, it asks you to indicate what each column means.
6. For **test** spreadsheets, a confirmation screen lists each output with a suggested task (classification or regression) and a few example values. Check the suggestion, change it if needed and click **Importar**. Training spreadsheets skip this step.
7. Click **Ver dashboard** to see the curves and metrics. For multi-output experiments, use the **Saída** selector to switch between outputs.

---

## Spreadsheet requirements

The import only works correctly if the spreadsheets follow the rules below. Most of them are checked when the file is uploaded. A few are not checked yet (see [Planned](#features)), and breaking them can make the import fail or produce wrong charts.

### General rules (both spreadsheets)

| Rule               | Details                                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| File format        | `.csv`, `.xlsx` or `.xls`                                                                                               |
| CSV separator      | Comma (`,`) or semicolon (`;`), detected automatically                                                                  |
| Encoding           | UTF-8 (with or without BOM)                                                                                             |
| Header             | The **first row** must contain the column names. No title rows, blank rows or merged cells above it                     |
| One table per file | Only the data table: no totals, notes or charts in the same sheet. In Excel files, only the first sheet is read         |
| Column names       | Case-insensitive (`Train_Loss` and `train_loss` are the same). Extra columns that are not recognized are ignored        |
| Decimal separator  | **Dot** (`0.25`), not comma (`0,25`). Spreadsheets exported by Excel in Portuguese use commas and are not supported yet |
| Numbers            | Numeric columns must contain only numbers. Text such as `n/a`, `-` or `inf` breaks the import                           |
| Empty cells        | Allowed only in optional columns                                                                                        |
| Re-import          | Importing a spreadsheet of the same type again **replaces** the previous data of that experiment                        |

### Training spreadsheet

One row per epoch (or per iteration).

| Column                 | Required | Type    | Description                                                                                                                                                           |
| ---------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `epoch` or `iteration` | Yes      | Integer | Step number. It must match the experiment's step unit: `epoch` for per-epoch experiments, `iteration` for per-iteration experiments. Each value must appear only once |
| `train_loss`           | Yes      | Number  | Loss on the training set. Must be filled in on every row                                                                                                              |
| `val_loss`             | No       | Number  | Loss on the validation set. May be empty on rows without validation                                                                                                   |
| `learning_rate`        | No       | Number  | Learning rate at that step                                                                                                                                            |
| `train_<metric>`       | No       | Number  | Any training metric, e.g. `train_accuracy`, `train_f1`, `train_mae`                                                                                                   |
| `val_<metric>`         | No       | Number  | Any validation metric, e.g. `val_accuracy`, `val_f1`, `val_mae`                                                                                                       |

Rules for the metric columns:

- Columns starting with `train_` or `val_` (other than the two losses) are recognized as metrics automatically. There is no need to register them beforehand.
- The text after the prefix becomes the metric name. To show training and validation of the same metric on one chart, use **the same name after the prefix**: `train_accuracy` and `val_accuracy` become the metric `accuracy`. `train_acc` and `val_accuracy` would be two different metrics.
- Empty cells in metric columns are skipped. This is normal when validation does not run at every step.
- The rows do not need to be in order: the charts sort them by step.

Example:

```csv
epoch,train_loss,val_loss,learning_rate,train_accuracy,val_accuracy
1,0.92,0.85,0.001,0.61,0.64
2,0.71,0.69,0.001,0.72,0.70
3,0.55,0.62,0.0005,0.80,0.74
```

Per-iteration example, with validation every 100 iterations:

```csv
iteration,train_loss,val_loss
100,1.20,1.15
150,1.05,
200,0.96,0.98
250,0.90,
```

**Multi-output networks:** use `train_loss` and `val_loss` for the total loss, and add the output name to the end of each output's loss and metrics. They are recognized as regular metrics:

```csv
epoch,train_loss,val_loss,train_loss_disease,val_loss_disease,train_loss_age,val_loss_age,train_accuracy_disease,val_accuracy_disease,train_mae_age,val_mae_age
```

### Test spreadsheet

One row per test set sample. Two formats are accepted.

**Single output**

| Column            | Required | Description                                                       |
| ----------------- | -------- | ----------------------------------------------------------------- |
| `sample_id`       | Yes      | Sample identifier, e.g. the image file name. Should be unique     |
| `true_label`      | Yes      | True value: the class (classification) or the number (regression) |
| `predicted_label` | Yes      | Value predicted by the model                                      |

The data is stored as one output named `principal`.

```csv
sample_id,true_label,predicted_label
img_0001.png,cat,cat
img_0002.png,dog,cat
img_0003.png,dog,dog
```

**Multiple outputs**

`sample_id` plus one pair of columns per output: `true_<output>` and `pred_<output>`. The text after the prefix is the output name, and it must be the same in both columns.

| Column          | Required            | Description                     |
| --------------- | ------------------- | ------------------------------- |
| `sample_id`     | Yes                 | Sample identifier               |
| `true_<output>` | Yes, one per output | True value of that output       |
| `pred_<output>` | Yes, one per output | Value predicted for that output |

```csv
sample_id,true_disease,pred_disease,true_age,pred_age
img_0001.png,rust,rust,34.5,31.2
img_0002.png,healthy,spot,52.0,49.8
img_0003.png,spot,spot,18.0,22.1
```

This spreadsheet creates two outputs, `disease` and `age`, each with three predictions. A cell may be left empty when a sample has no label for one of the outputs: that row is skipped for that output only. An output whose columns are empty on every row is ignored.

The multi-output format is used whenever the spreadsheet has at least one `true_<output>` / `pred_<output>` pair. Do not mix it with `true_label` / `predicted_label` in the same file: in that case, the `true_label` columns are ignored.

**Choosing the task of each output**

There is no task to choose when creating the experiment. After a test spreadsheet is uploaded, a confirmation screen shows each output with a **suggested task** and up to five example values. The suggestion is computed from the values (true and predicted together):

1. If there is any **text**, it suggests **classification**.
2. If there are only **integers** with **at most 20 distinct values**, it suggests **classification** (e.g. class ids `0` to `9`).
3. Otherwise, it suggests **regression**.

The suggestion is right in most cases, but it should be changed on the confirmation screen in these:

| Case                                                                              | Suggested      | Choose                                          |
| --------------------------------------------------------------------------------- | -------------- | ----------------------------------------------- |
| Classification with more than 20 numeric class ids (e.g. CIFAR-100)               | Regression     | Classification                                  |
| Regression with integer targets and few distinct values (e.g. ages from 18 to 32) | Classification | Regression                                      |
| Regression with text in a cell (`n/a`)                                            | Classification | Regression, after removing the text (see below) |

For binary classification, export the predicted **class** (`0` or `1`), not the predicted probability (`0.87`): a probability is not a class, whatever task is chosen.

**Classification rules**

- Labels can be text (`cat`) or numbers (`0`, `1`, `2`).
- Labels are compared exactly, so the spelling must be identical in both columns: `cat`, `Cat` and `cat ` (with a trailing space) are three different classes. Spaces at the start and end of a label are removed.

**Regression rules**

- True and predicted values must be numbers. If an output marked as regression has text in any cell, the import is rejected and the message lists the rows with problems. Fix them and upload the file again.
- Samples whose true value is `0` are left out of the MRE (relative error), since the error cannot be divided by zero. The other metrics use all samples.

### Checklist before importing

- [ ] The first row has the column names, with nothing above it.
- [ ] The step column is `epoch` or `iteration`, matching the experiment.
- [ ] Decimal numbers use a dot.
- [ ] Numeric columns have no text (`n/a`, `-`, `inf`).
- [ ] Training and validation metrics use the same name after `train_` / `val_`.
- [ ] In multi-output test spreadsheets, every `true_<output>` has a `pred_<output>` with the same name.
- [ ] Classification outputs contain classes, not probabilities.
- [ ] In classification, class names are spelled the same way in both columns.
- [ ] On the confirmation screen, the task of each output is the right one.

### Common problems

| Message or symptom                                                                 | Cause                                                                           | Fix                                                                   |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| The column mapping screen appears                                                  | Column names do not follow the convention                                       | Indicate each column on the screen, or rename the columns in the file |
| The import fails on a training spreadsheet                                         | Decimal commas or text in numeric columns                                       | Export the file with dots as decimal separator and remove the text    |
| A metric appears twice on the dashboard                                            | Different names after `train_` and `val_`                                       | Use the same name, e.g. `train_f1` and `val_f1`                       |
| The confusion matrix has unexpected classes                                        | Different spellings of the same class                                           | Standardize the class names                                           |
| A regression output shows a confusion matrix, or a classification output shows MAE | The wrong task was confirmed on the confirmation screen                         | Import the spreadsheet again and choose the right task                |
| "A saída '…' foi marcada como regressão, mas … tem valores que não são números"    | An output marked as regression has text in some cells                           | Fix the listed rows, or choose classification if that is the task     |
| An output is missing from the selector                                             | Its `true_` and `pred_` columns have different names, or one of them is missing | Use `true_<output>` and `pred_<output>` with the same name            |
| "A planilha precisa da coluna sample_id."                                          | Multi-output spreadsheet without a `sample_id` column                           | Rename the identifier column to `sample_id`                           |

---

## Project structure

```
deep-viewer/
├── config/                      # Django settings and root URLs
├── accounts/                    # users: landing page, sign-up, login and profile
│   └── services/
│       └── institutions.py      # institution search (ROR API)
├── experiments/                 # projects, experiments and spreadsheet import
│   ├── models.py                # database entities
│   ├── forms/                   # project, experiment, upload, column mapping and output task forms
│   ├── views/                   # project, experiment and import screens (upload, columns, confirmation)
│   ├── urls.py
│   ├── admin.py
│   └── services/
│       ├── exceptions.py        # ImportValidationError
│       ├── parsing.py           # spreadsheet reading, column recognition and task suggestion
│       └── importing.py         # saving the data to the database
├── analyses/                    # dashboard: metrics and charts
│   ├── services/
│   │   ├── metrics.py           # classification and regression metrics
│   │   ├── ranking.py           # output ranking
│   │   └── charts.py            # Plotly charts
│   ├── templatetags/            # loss preview curve on the experiment cards
│   └── tests/
├── templates/                   # HTML templates for all screens
├── static/                      # CSS and JavaScript
├── media/                       # uploaded spreadsheets (not versioned)
├── manage.py
└── requirements.txt
```

The business logic is kept separate from the views, in each app's `services/` folder:

- `parsing.py` uses pandas and never touches the database: it reads the file, checks the column names and the values, finds the outputs of the test spreadsheet, suggests the task of each one and splits the data into the parts that go into each table. The single-output format is converted into the multi-output one (`true_principal` / `pred_principal`) right after the columns are known, so the rest of the code handles a single format. Problems found in the spreadsheet raise `ImportValidationError`, whose messages are shown on the form;
- `importing.py` coordinates the import and saves the data to the database inside a transaction (either everything is saved, or nothing is). Every step returns the next one (`mapping`, `tasks` or `done`), and the views only follow it;
- `metrics.py` computes the metrics of one output by hand; the tests compare the results with scikit-learn.

### Import flow

```
upload ─→ columns recognized? ── no ─→ column mapping screen ─┐
               │                                              │
              yes ←───────────────────────────────────────────┘
               │
       training spreadsheet ─→ saved
       test spreadsheet ─────→ task confirmation screen ─→ saved ─→ dashboard
```

Between screens, the uploaded file is kept on disk and the pending import is kept in the user's session.

### Data model

```
User
 └── Project
      └── Experiment                       (step unit: epoch or iteration)
           ├── Hyperparameter
           ├── ImportedFile
           ├── TrainingStep                (one row of the training spreadsheet)
           │    └── StepMetric             (one metric of that row)
           └── Output                      (one output of the network, with its task)
                ├── ClassificationPrediction   (one sample of a classification output)
                └── RegressionPrediction       (one sample of a regression output)
```

The task (classification or regression) belongs to each **output**, not to the experiment. A single-output experiment has one output named `principal`; a multi-output experiment has one output per `true_` / `pred_` pair. Each row of the test spreadsheet becomes one prediction **for each output**.

---

## Tests

```bash
python manage.py test
```

---

## Authors

- Carlos
- João Pedro
