# roundtable

`roundtable` is a tool that simulates a roundtable discussion using AI agents.

## Installation

This tool uses [poetry](https://python-poetry.org/) to manage dependencies and packaging. To install all the
dependencies simply run:

``` shell
poetry install
```

### Using ollama

```shell
ollama pull 'your_model'
```

## Usage

You can run the tool using poetry:

``` shell
poetry run roundtable --help
```

Or you can run the tool using python:

``` shell
python -m roundtable --help
```

Or you can run the tool directly from the directory or add it to your path:

``` shell
roundtable --help
```

```shell
usage: roundtable [-h] [--verbose] [--debug] [--quiet | --no-quiet | -q] [--version] [--cli]

This is a template repository to build Python CLI tool.

options:
  -h, --help            show this help message and exit
  --verbose, -v         Increase verbosity. Use more than once to increase verbosity level (e.g. -vvv).
  --debug               Enable debug mode.
  --quiet, --no-quiet, -q
                        Do not print any output/log
  --version             Show version and exit.
  --cli                 Run the tool in CLI mode.
```

## Development

### Testing

To run the tests simply run:

``` shell
poetry run test
```

### Update `setup.py`

To update the `setup.py` file with the latest dependencies and versions run:

``` shell
poetry run poetry2setup > setup.py
```

### Acknowledgements

This project was generated using powerful tools and libraries such as [poetry](https://python-poetry.org/),
[pydantic](https://docs.pydantic.dev/latest/), [pytest](https://docs.pytest.org/en/stable/) and more, I simply put the
pieces together. Please check and support all the tools and libraries used in this project.