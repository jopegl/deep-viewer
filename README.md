# Deep Viewer

A web application for recording and analyzing deep learning training experiments.

Researchers organize their studies into **projects**, register each training run as an **experiment**, and import two spreadsheets produced by their training code (PyTorch): the **training log** (loss and metrics per epoch or iteration) and the **test set results** (true and predicted value per sample). From these, the system generates learning curves, test metrics and comparisons between experiments.

Developed for the **DCC061 – Software Engineering** course.

> **Status:** in development.

---

## Features

**Implemented**

- Landing page, sign-up, login and profile editing
- Institution search on sign-up and profile, using the [ROR](https://ror.org) registry
- Every page requires login; the admin panel is only available to staff users
- Projects and experiments (classification or regression, per epoch or per iteration)
- Import of training and test spreadsheets (CSV or Excel)
- Automatic column recognition when the spreadsheet follows the naming convention
- Column mapping screen when the spreadsheet uses different names
- Re-import: uploading a spreadsheet again replaces the previous data
- Experiment dashboard:
  - training vs. validation curves for the loss and for every metric
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
3. Inside the project, create an **experiment**, choosing its task (classification or regression) and its step unit (epoch or iteration).
4. Click **Importar planilhas**, choose the spreadsheet type (train or test), select the file and click **Importar**.
5. If the column names follow the convention below, the data is imported right away. Otherwise, the system asks you to indicate what each column means.
6. Click **Ver dashboard** to see the curves and metrics.

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

### Test spreadsheet

One row per test set sample. The content depends on the experiment's task, and **the spreadsheet must match the task chosen when the experiment was created**. A classification spreadsheet imported into a regression experiment is rejected.

| Column            | Required | Description                                                       |
| ----------------- | -------- | ----------------------------------------------------------------- |
| `sample_id`       | Yes      | Sample identifier, e.g. the image file name. Should be unique     |
| `true_label`      | Yes      | True value: the class (classification) or the number (regression) |
| `predicted_label` | Yes      | Value predicted by the model                                      |

**Classification**

- Labels can be text (`cat`) or numbers (`0`, `1`, `2`).
- Labels are compared exactly, so the spelling must be identical in both columns: `cat`, `Cat` and `cat ` (with a trailing space) are three different classes.
- Every row must have both labels filled in.

```csv
sample_id,true_label,predicted_label
img_0001.png,cat,cat
img_0002.png,dog,cat
img_0003.png,dog,dog
```

**Regression**

- `true_label` and `predicted_label` must be numbers on every row. If any cell contains text, the import is rejected and the message lists the rows with problems.
- Samples whose true value is `0` are left out of the MRE (relative error), since the error cannot be divided by zero. The other metrics use all samples.

```csv
sample_id,true_label,predicted_label
s0001,11.33,18.35
s0002,36.19,38.39
s0003,8.12,17.88
```

### Checklist before importing

- [ ] The first row has the column names, with nothing above it.
- [ ] The step column is `epoch` or `iteration`, matching the experiment.
- [ ] Decimal numbers use a dot.
- [ ] Numeric columns have no text (`n/a`, `-`, `inf`).
- [ ] Training and validation metrics use the same name after `train_` / `val_`.
- [ ] The test spreadsheet matches the experiment's task (classification or regression).
- [ ] In classification, class names are spelled the same way in both columns.

### Common problems

| Message or symptom                          | Cause                                                                                                                            | Fix                                                                   |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| The column mapping screen appears           | Column names do not follow the convention                                                                                        | Indicate each column on the screen, or rename the columns in the file |
| "têm valores que não são números"           | Text in a numeric column of a regression test spreadsheet, or a classification spreadsheet imported into a regression experiment | Fix the listed rows, or create a classification experiment            |
| The import fails on a training spreadsheet  | Decimal commas or text in numeric columns                                                                                        | Export the file with dots as decimal separator and remove the text    |
| A metric appears twice on the dashboard     | Different names after `train_` and `val_`                                                                                        | Use the same name, e.g. `train_f1` and `val_f1`                       |
| The confusion matrix has unexpected classes | Different spellings of the same class                                                                                            | Standardize the class names                                           |

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
│   ├── forms/                   # project, experiment, upload and column mapping forms
│   ├── views/                   # project, experiment and import screens
│   ├── urls.py
│   ├── admin.py
│   └── services/
│       ├── exceptions.py        # ImportValidationError
│       ├── parsing.py           # spreadsheet reading and column recognition
│       └── importing.py         # saving the data to the database
├── analyses/                    # dashboard: metrics and charts
│   ├── services/
│   │   ├── metrics.py           # classification and regression metrics
│   │   ├── ranking.py           # experiment ranking
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

- `parsing.py` uses only pandas: it reads the file, checks the column names and the values, and splits the data into the parts that go into each table. Problems found in the spreadsheet raise `ImportValidationError`, whose messages are shown on the form;
- `importing.py` saves that data to the database inside a transaction (either everything is saved, or nothing is);
- `metrics.py` computes the metrics by hand; the tests compare the results with scikit-learn.

### Data model

```
User
 └── Project
      └── Experiment
           ├── Hyperparameter
           ├── ImportedFile
           ├── TrainingStep               (one row of the training spreadsheet)
           │    └── StepMetric            (one metric of that row)
           ├── ClassificationPrediction   (one row of the test spreadsheet, classification)
           └── RegressionPrediction       (one row of the test spreadsheet, regression)
```

---

## Tests

```bash
python manage.py test
```

---

## Authors

- Carlos
- João Pedro
