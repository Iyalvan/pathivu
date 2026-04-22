# pathivu

record immutable git and build intel into your python artifacts.

*pathivu* (Tamil: பதிவு) means "record" or "entry" — a permanent log of what
an artifact is, inscribed into the artifact itself at build time.

once a wheel or docker image is built, it is often hard to tell what exactly
is in it: which commit, which tag, when it was built, what dependencies
resolved. `pathivu` runs right before the build and writes an `_about.json`
inside your package. your app reads it back at runtime — e.g. through a
simple `/about` endpoint — so the artifact can describe itself.

## install

```bash
pip install pathivu
# with adapters:
pip install "pathivu[fastapi]"
pip install "pathivu[flask]"
```

## use

at build time:

```bash
pathivu my-api "I serve users"
# writes src/my_api/_about.json
python -m build
```

at runtime:

```python
from pathivu import read_about
about = read_about("my_api")
```

## what the about file looks like

```json
{
  "about": { "app_name": "my-api", "description": "I serve users" },
  "git": {
    "commit_id": "4fc2eea",
    "version_tag": "v0.1.0",
    "branch": "main",
    "repo_url": "git@github.com:you/my-api.git",
    "commit_time": "2026-04-21T15:28:40+05:30",
    "author": "You",
    "message": "initial: bootstrap"
  },
  "pkg": { "name": "my-api", "version": "0.1.0", "description": "..." },
  "deps": {
    "fastapi": {
      "version": "0.136.0",
      "depends_on": { "starlette": { "version": "1.0.0" }, "pydantic": { "...": "..." } }
    }
  },
  "described_at": "2026-04-21T09:58:55+00:00"
}
```

missing pieces (no git, no tag, no pyproject) are omitted — `pathivu` never
blocks a build on missing intel. it is observational, not prescriptive.

## wiring it into your build

### uv

```bash
pathivu my-api "desc" && uv build
```

### hatch

```bash
pathivu my-api "desc" && hatch build
```

### poetry

```bash
pathivu my-api "desc" && poetry build
```

### setuptools / build

```bash
pathivu my-api "desc" && python -m build
```

### makefile (tool-agnostic)

```makefile
build:
	pathivu my-api "$$(git log -1 --pretty=%s)" && python -m build
```

### making sure `_about.json` lands in the wheel

`pathivu` writes to `src/<pkg>/_about.json` by default. if you use the
standard `src` layout with hatchling / setuptools / poetry, package data
under the package directory is included automatically. for unusual layouts,
pass `--out <path>` to pathivu and adjust your build tool's include rules
accordingly.

## reading it back in a web app

### fastapi

```python
from fastapi import FastAPI
from pathivu.frameworks.fastapi import about_router

app = FastAPI()
app.include_router(about_router("my_api"))
# GET /about -> the full about dict
```

custom path:

```python
app.include_router(about_router("my_api", path="/meta"))
```

### flask

```python
from flask import Flask
from pathivu.frameworks.flask import about_blueprint

app = Flask(__name__)
app.register_blueprint(about_blueprint("my_api"))
```

### any framework (manual)

```python
from pathivu import read_about
about = read_about("my_api")  # returns a dict; you handle serving it
```

## cli reference

```
pathivu <app-name> [description]
    [--out PATH]                 custom output path
    [--pyproject PATH]           pyproject.toml location (default ./pyproject.toml)
    [--exclude-transitive list]  comma-separated deps whose subtree collapses to "..."
```

`python -m pathivu ...` is equivalent.

## develop

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## license

MIT
