# Bibtex Autocomplete

This repository contains a python package to autocomplete bibliographies by finding missing DOIs and URLs.

It is inspired and expanding on the solution provided by [thando](https://tex.stackexchange.com/users/182467/thando) in this [tex stackexchange post](https://tex.stackexchange.com/questions/6810/automatically-adding-doi-fields-to-a-hand-made-bibliography).

It attempts to complete a bibtex file by querying the following domains:
- [www.crossref.org](https://www.crossref.org)
- [dlbp.org](https://dlbp.org)
- [researchr.org](https://researchr.org/)
- [unpaywall.org](https://unpaywall.org/)

The searches are performed using the entries' dois if present, title or author otherwise. The titles are compared excluding punctuation and case. Make sure your titles are correct to get matches.

## Installation

### Quick install

Using `pip` NOT YET IMPLEMENTED

### Manual install

Using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) (`python3 -m pip install venv`) :

```
git clone https://github.com/dlesbre/bibtex-autocomplete.git &&
cd bibtex-autocomplete &&
python3 -m venv venv &&
source venv/bin/activate &&
make setup
```

You should now be able to run the script using either commands:

```
python3 -m bibtexautocomplete --version
bibtexautocomplete --version
```

This will install all dependencies required for running the script in `./venv/`. Optional dependencies used for development and testing can be installed by running `make setup-dev`.

### Dependencies

This package has two dependencies (automatically installed if using [quick-install](#quick-install)) :

- [bibtexparser](https://bibtexparser.readthedocs.io/)
- [alive_progress](https://github.com/rsalmei/alive-progress) for the fancy progressbar

## Usage

The command line tool can be used as follows:

```
bibtexautocomplete version 0.2
Program to autocomplete bibtex entries by searching online databases.
Polls the following databases:
  ['crossref', 'dblp', 'researchr', 'unpaywall']

Usage:
  bibtexautocomplete [--flags] <input_files>

Example:
  bibtexautocomplete my_bib.bib         print to stdout
  bibtexautocomplete -i my_bib.bib      inplace modify
  bibtexautocomplete a.bib -o b.bib c.bib -o d.bib
      writes completed a.bib in b.bib and c.bib in d.bib

Optional arguments: can all be used multiple times
  -o --output <file>          Write output to given file
            With multiple input/outputs they are mapped in appearance order
            Extra inputs are dumped on stdout

  -q --only-query <site>      Only query the given sites
  -Q --dont-query <site>      Don't query the given sites
            Site must be one of: ['crossref', 'dblp', 'researchr', 'unpaywall']

  -e --only-entry    <id>     Only perform lookup these entries
  -E --exclude-entry <id>     Don't perform lookup these entries
            ID is the identifier in bibtex (e.g. @inproceedings{<id> ... })

  -c --only-complete <field>  Only complete the given fields
  -C --dont-complete <field>  Don't complete the given fields
            Field is a bibtex field (e.g. 'author', 'doi',...)

Flags:
  -i --inplace          Modify input files inplace, overrides any specified output files
  -f --force-overwrite  Overwrite aldready present fields with data found online
  -t --timeout <float>  set timeout on request, default: 10.0 s

  -v --verbose          print the commands called
  -s --silent           don't show progressbar (keeps tex output and error messages)
  -n --no-color         don't color output

  --version             show version number
  -h --help             show this help
```
