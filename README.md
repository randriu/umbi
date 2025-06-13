# umbi

Library for input/output of transition systems in a *unified Markov binary (UMB)* format.

## Installation:

(optional) create and activate a python environment:

```
$ python -m venv venv
$ source venv/bin/activate
```

Install `umbi` via
```
(venv) $ pip install umbi
```

## Running umbi

Examples:
```
(venv) $ umbi --import-umb /path/to/input.umb
(venv) $ umbi --import-umb /path/to/input.umb --export-umb /path/to/output.umb
(venv) $ umbi --import-umb /path/to/input.umb --export-umb /path/to/output.umb --log-level=DEBUG
```
