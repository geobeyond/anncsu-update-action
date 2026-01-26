# ANNCSU Update action

> ANNCSU DB update from Geodiff reports

A GitHub Action to update ANNCSU db via openapi interface using anncsu-sdk. Updates are guided by an input Geodiff report file.

## Features

- Parse geodiff JSON report
- Update ANNCSU db via openapi interface using anncsu-sdk guided by the Geodiff report
  - Manage Insert, Update, Delete of addresses
- Triggered when used inside a step of a more compex action. Common use follow these steps:
  - Triggered when push on **/*.duckdb file
  - Execute extract-duckdb-table
  - geodiff-action
  - anncsu-update-action
- Triggered also or manually via `workflow_dispatch`

## Workflow

The workflow is defined in [.github/workflows/anncsu-update.yml](.github/workflows/extract-duckdb.yml).

- Triggers: `push` on `**/*.duckdb` and `workflow_dispatch` for manual runs.
- Environment: `ubuntu-latest` runner.

### Inputs (manual run)

- `geodiff_report` (required): Geodiff JSON report.

### Behavior

- On push: the workflow locates the first `.duckdb` file changed in the commit and extracts the requested table.
- On manual dispatch: provide `geodiff_report` in the Run workflow form.
- Outputs:  report.

## Usage examples

Manual run (UI): go to the Actions tab, pick "Anncsu Update", click "Run workflow" and set `geodiff_report` json.

Programmatic example (manual workflow_dispatch in another workflow using `workflow_call` or via API):

```yaml
# Example consumer workflow (concept)
name: Invoke Extract
on:
  workflow_dispatch:
    inputs:
      geodiff_report:
        required: true
jobs:
  call:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger anncsu update
        run: echo "Use repository dispatch or call the workflow from the UI with table_name=${{ github.event.inputs.geodiff_report }}"
```

## Notes

- The workflow expects `geodiff_report` via `workflow_dispatch` input or an environment variable; for fully automated push-based execution you may add it as a step in a more structured action — see the [Features](#features) paragraph.

## Development

Follow the existing development instructions in this README for running tests and linters locally.
