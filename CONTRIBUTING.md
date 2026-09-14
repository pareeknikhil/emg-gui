# Contributing

Contributions are welcome. Before submitting a pull request, run the relevant
linters for the files you changed.

## Run Super-Linter Locally

### Run All Linters

From the project root, run all supported linters using Docker:

```bash
sudo docker run --rm -e RUN_LOCAL=true -e DEFAULT_BRANCH=main -e VALIDATE_ALL_CODEBASE=true -v "$PWD":/tmp/lint ghcr.io/super-linter/super-linter:v8.7.0
```

### Run a Specific Linter

Set the relevant `VALIDATE_<LINTER_NAME>` environment variable to `true`. For
example, to run only Ruff:

```bash
sudo docker run --rm -e RUN_LOCAL=true -e DEFAULT_BRANCH=main -e VALIDATE_ALL_CODEBASE=true -e VALIDATE_PYTHON_RUFF=true -v "$PWD":/tmp/lint ghcr.io/super-linter/super-linter:v8.7.0
```
