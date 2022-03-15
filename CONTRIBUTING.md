# Contributing

Any contributions are welcome !

## Issues

Use the [github issue tracker](https://github.com/dlesbre/bibtex-autocomplete/issues) to report bugs, request new features or open any discussion about the project.
- Please check if a similar issue already exists before opening a new one
- For bug reports, try to include version information, steps to reproduce and a minimal example

## Pull requests guidelines

To quickly setup the project. I recommand using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) (`python3 -m pip install venv`) to keep dependencies separate:

```
git clone https://github.com/dlesbre/bibtex-autocomplete.git &&
cd bibtex-autocomplete &&
python3 -m venv venv &&
source venv/bin/activate &&
make setup-dev
```

This will install the code and dependencies, including the [mypy](http://mypy-lang.org/) type-checker and [black](https://pypi.org/project/black/) formatter. It will also set a pre-commit hook to run these before you commit, to auto-format code and identify errors.

You can contribute code via the fork/pull request method.
- By doing so you agree to deploy your code under an MIT License
- Please make sure you pass typechecking (`make mypy`) and tests (`make test`) before submitting.
- Please respect coding style (`make format` will auto format the code with black and isort).
- Please add your changes to the CHANGELOG, a the top (in the `Version ???` section).
- For new features, consider writing tests to check their functionality.
