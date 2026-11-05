# Deep Viewer

A web application for recording and analyzing deep learning training experiments.

Researchers organize their studies into **projects**, register each training run as an **experiment**, and import two spreadsheets produced by their training code (PyTorch): the **training log** (loss and metrics per epoch or iteration) and the **test set results** (true and predicted value per sample). From these, the system generates learning curves, test metrics and comparisons between experiments.

Developed for the **DCC061 – Software Engineering** course.

> **Status:** in development.

---

## Features

**Implemented**

- User sign-up, login and profile editing
- Projects and experiments (classification or regression, per epoch or per iteration), with hyperparameters
- Import of training and test spreadsheets (CSV or Excel)
- Automatic column recognition when the spreadsheet follows the naming convention
- Column mapping screen when the spreadsheet uses different names
- Re-import: uploading a spreadsheet again replaces the previous data

**Planned**

- Screens to create and manage projects and experiments (currently done through the admin panel)
- Detailed spreadsheet validation, reporting the row of each error
- Training vs. validation curves
- Classification metrics (accuracy, precision, recall, F1) and confusion matrix
- Regression metrics (MAE, RMSE, R²) and true vs. predicted plot
- Experiment ranking and comparison
- PDF report

---

## Tech stack

- Python 3.12
- Django
- pandas and openpyxl (spreadsheet reading)
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

**5. Create an admin user**

```bash
python manage.py createsuperuser
```

**6. Start the server**

```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000/accounts/login/ in your browser. The admin panel is at http://127.0.0.1:8000/admin/.

---

## Usage

1. Log in.
2. In the admin panel, create a **project** and, inside it, an **experiment**, choosing its task (classification or regression) and step unit (epoch or iteration).
3. Open the experiment's import page: `http://127.0.0.1:8000/experiments/<id>/import/`.
4. Choose the spreadsheet type (train or test), select the file and click **Importar**.
5. If the column names follow the convention below, the data is imported right away. Otherwise, the system asks you to indicate what each column means.

---

## Spreadsheet format

Accepted files are `.csv` (comma or semicolon separated), `.xlsx` and `.xls`. Column names are case-insensitive.

### Training spreadsheet

One row per epoch (or per iteration).

| Column                 | Required | Description                                                                                      |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------ |
| `epoch` or `iteration` | Yes      | Step number. Use `epoch` for per-epoch experiments and `iteration` for per-iteration experiments |
| `train_loss`           | Yes      | Loss on the training set                                                                         |
| `val_loss`             | No       | Loss on the validation set. May be empty on rows without validation                              |
| `learning_rate`        | No       | Learning rate at that step                                                                       |
| `train_<metric>`       | No       | Any training metric, e.g. `train_accuracy`, `train_f1`, `train_mae`                              |
| `val_<metric>`         | No       | Any validation metric, e.g. `val_accuracy`, `val_f1`, `val_mae`                                  |

Columns starting with `train_` or `val_` (other than the losses) are automatically recognized as metrics. There is no need to register them beforehand.

Example:

```csv
epoch,train_loss,val_loss,learning_rate,train_accuracy,val_accuracy
1,0.92,0.85,0.001,0.61,0.64
2,0.71,0.69,0.001,0.72,0.70
3,0.55,0.62,0.0005,0.80,0.74
```

### Test spreadsheet

One row per test set sample.

| Column            | Required | Description                                                       |
| ----------------- | -------- | ----------------------------------------------------------------- |
| `sample_id`       | Yes      | Sample identifier (e.g. the image file name)                      |
| `true_label`      | Yes      | True value: the class (classification) or the number (regression) |
| `predicted_label` | Yes      | Value predicted by the model                                      |

Example (classification):

```csv
sample_id,true_label,predicted_label
img_0001.png,cat,cat
img_0002.png,dog,cat
img_0003.png,dog,dog
```

Example (regression):

```csv
sample_id,true_label,predicted_label
s0001,11.33,18.35
s0002,36.19,38.39
s0003,8.12,17.88
```

---

## Project structure

```
deep-viewer/
├── config/                  # Django settings and root URLs
├── accounts/                # users: sign-up, login and profile
├── experiments/             # projects, experiments and spreadsheet import
│   ├── models.py            # database entities
│   ├── forms.py             # upload and column mapping forms
│   ├── views.py             # import screens
│   ├── urls.py
│   ├── admin.py
│   └── services/
│       ├── parsing.py       # spreadsheet reading and column recognition
│       └── importing.py     # saving the data to the database
├── templates/               # HTML templates for all screens
├── media/                   # uploaded spreadsheets (not versioned)
├── manage.py
└── requirements.txt
```

The import logic is kept separate from the views, in `experiments/services/`:

- `parsing.py` uses only pandas: it reads the file, checks the column names and splits the data into the parts that go into each table;
- `importing.py` saves that data to the database inside a transaction (either everything is saved, or nothing is).

### Data model

```
Project
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
