# emg-gui

## 1. Overview

TODO

---

## 2. Project Structure

Inside this project, you'll see the following folders and files:

```text
/
├── src/
│   └── emg_gui/
│       ├── app.py
│       ├── configs/
│       ├── core/
│       ├── shaders/
│       ├── utils/
│       └── visualizer/
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 3. Setup

### 3.1 Using pip and requirements.txt

TODO

### 3.2 Using Poetry

TODO

---

## 4. How to Run

TODO

---

## 5. Run Super-Linter Locally

### 5.1 Run All Linters

From the project root, run all supported linters using Docker:

```bash
sudo docker run --rm -e RUN_LOCAL=true -e DEFAULT_BRANCH=main -e VALIDATE_ALL_CODEBASE=true -v "$PWD":/tmp/lint ghcr.io/super-linter/super-linter:v8.7.0
```

### 5.2 Run a Specific Linter

Set the relevant `VALIDATE_<LINTER_NAME>` environment variable to `true`. For example, to run only Ruff:

```bash
sudo docker run --rm -e RUN_LOCAL=true -e DEFAULT_BRANCH=main -e VALIDATE_ALL_CODEBASE=true -e VALIDATE_PYTHON_RUFF=true -v "$PWD":/tmp/lint ghcr.io/super-linter/super-linter:v8.7.0
```

---

## 6. Tech Debt

1. Fix lints.
2. Add code setup details to this README.
3. Update the GUI so switching between test, train, and validate dynamically updates the folder dropdown options.
