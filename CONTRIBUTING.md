# Contributing

Any contributions are welcome !

## Issues

Use the [github issue tracker](https://github.com/dlesbre/bibtex-autocomplete/issues)
to report bugs, request new features or open any discussion about the project.
- Please check if a similar issue already exists before opening a new one
- For bug reports, try to include version information (for `btac` and `python`),
  operating system, steps to reproduce and a minimal example.

  Note: if `btac` crashes on a large file, you can use verbose mode (`-v`
  option) to find the offending entry. This prints entries as they are completed
  so the first entry that isn't printed is likely the problematic one (it might
  also be one of the next ones because of multithreading). You can confirm this
  using the `-e suspect_entry` option to only try completing this entry.

## Pull requests guidelines

To quickly setup the project. I recommend using a [virtual
environment](https://docs.python.org/3/tutorial/venv.html) (`python3 -m pip
install venv`) to keep dependencies separate:

```
git clone https://github.com/dlesbre/bibtex-autocomplete.git &&
cd bibtex-autocomplete &&
python3 -m venv venv &&
source venv/bin/activate &&
make setup-dev
```

This will install the code and dependencies, including the [mypy](http://mypy-lang.org/) type-checker and [ruff](https://docs.astral.sh/ruff/) linter/formatter. It will also set a pre-commit hook to run these before you commit, to auto-format code and identify errors.

You can contribute code via the fork/pull request method.
- By doing so you agree to deploy your code under an MIT License
- Please make sure you pass type-checking (`make mypy`) and tests (`make test`) before submitting.
- Please respect coding style (`make format` will auto format the code with ruff).
- Please add your changes to the CHANGELOG, at the top (in the `Unreleased` section).
- For new features, consider writing tests to check their functionality.
