# Bibtex Autocomplete

This repository contains a python package to autocomplete bibliographies by finding missing DOIs and URLs.

It is inspired and expanding on the solution provided by [thando](https://tex.stackexchange.com/users/182467/thando) in this [tex stackexchange post](https://tex.stackexchange.com/questions/6810/automatically-adding-doi-fields-to-a-hand-made-bibliography).

## Installation

### Quick install

Using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) (`python3 -m pip install venv`) :

```
git clone https://github.com/dlesbre/bibtex-autocomplete.git &&
cd bibtex-autocomplete &&
python3 -m venv venv &&
source venv/bin/activate &&
make setup
```

This will install all dependencies required for running the script in `./venv/`. Optional dependencies used for development and testing can be installed by running `make setup-dev`.


TODO
- fix setup
- read files
- script
- inplace flag
- doi first search
- tests
- README
- contributing
- progressbar
- pipable
- __init__
