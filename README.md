# Bibtex Autocomplete

[![PyPI version][version-shield]][pypi-link]
[![PyPI pyversions][pyversion-shield]][pypi-link]
[![License][license-shield]](https://choosealicense.com/licenses/mit/)
[![PyPI status][status-shield]][pypi-link]
[![Downloads][download-shield]](https://pepy.tech/project/bibtexautocomplete)

[![Maintenance][maintain-shield]][commit-link]
[![Commit][commit-shield]][commit-link]
[![actions][pipeline-shield]][pipeline-link]
[![issues][issues-shield]][issues-link]
[![pull requests][pr-shield]][pr-link]

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10207744.svg)](https://doi.org/10.5281/zenodo.10207744)

[version-shield]:   https://img.shields.io/pypi/v/bibtexautocomplete.svg
[pyversion-shield]: https://img.shields.io/pypi/pyversions/bibtexautocomplete.svg
[license-shield]:   https://img.shields.io/pypi/l/bibtexautocomplete.svg
[status-shield]:    https://img.shields.io/pypi/status/bibtexautocomplete.svg
[download-shield]:  https://static.pepy.tech/badge/bibtexautocomplete
[pypi-link]: https://pypi.python.org/pypi/bibtexautocomplete/

[maintain-shield]: https://img.shields.io/badge/Maintained%3F-yes-brightgreen.svg
[commit-shield]: https://img.shields.io/github/last-commit/dlesbre/bibtex-autocomplete
[commit-link]: https://github.com/dlesbre/bibtex-autocomplete/graphs/commit-activity

[pipeline-shield]: https://img.shields.io/github/actions/workflow/status/dlesbre/bibtex-autocomplete/python-app.yml?branch=master&label=tests
[pipeline-link]: https://github.com/dlesbre/bibtex-autocomplete/actions/workflows/python-app.yml

[issues-shield]: https://img.shields.io/github/issues/dlesbre/bibtex-autocomplete
[issues-link]: https://github.com/dlesbre/bibtex-autocomplete/issues

[pr-shield]: https://img.shields.io/github/issues-pr/dlesbre/bibtex-autocomplete
[pr-link]: https://github.com/dlesbre/bibtex-autocomplete/pulls

**bibtex-autocomplete** or **btac** is a simple script to autocomplete BibTeX
bibliographies. It reads a BibTeX file and looks online for any additional data
to add to each entry. It can quickly generate entries from minimal data (a lone
title is often sufficient to generate a full entry). You can also use it to only
add specific fields (like DOIs, or ISSN) to a manually curated bib file.

It is designed to be as simple to use as possible: just give it a bib file and
let **btac** work its magic! It combines multiple sources and runs consistency
and normalization checks on the added fields (only adds URLs that lead to a valid
webpage, DOIs that exist at https://dx.doi.org/, ISSN/ISBN with valid check 
digits...).

It attempts to complete a BibTeX file by querying the following domains:
- [openalex.org](https://openalex.org/): ~240 million entries
- [www.crossref.org](https://www.crossref.org/): ~150 million entries
- [arxiv.org](https://arxiv.org/): open access archive, ~2.4 million entries
- [semanticscholar.org](https://www.semanticscholar.org/): ~215 million entries
- [unpaywall.org](https://unpaywall.org/): database of open access articles, ~48 million entries
- [dblp.org](https://dblp.org): computer science, ~7 million entries
- [researchr.org](https://researchr.org/): computer science
- [inspirehep.net](https://inspirehep.net/): high-energy physics, ~1.5 million entries

Big thanks to all of them for allowing open, easy and well-documented access to
their databases. This project wouldn't be possible without them. You can easily
narrow down the list of sources if some aren't relevant using [command line options](#query-filtering).

### Contents

- [Demo](#demo)
- [Quick overview](#quick-overview)
- [Installation](#installation)
  - [Shell tab completion](#shell-tab-completion)
  - [Dependencies](#dependencies)
- [Usage](#usage)
- [Command line arguments](#command-line-arguments)
  - [Specifying output](#specifying-output)
  - [Query filtering](#query-filtering)
  - [New field formatting](#new-field-formatting)
  - [Global output formatting](#global-output-formatting)
  - [Optional flags](#optional-flags)
- [Running from python](#running-from-python)
- [Credit and license](#credit-and-license)

## Demo

![demo.svg](https://raw.githubusercontent.com/dlesbre/bibtex-autocomplete/2d1a01f5ec94c8af9c2f3c1a810eca51bb4cce74/imgs/demo.svg)

## Quick overview

**How does it find matches?**

`btac` queries the websites using the entry DOI (if known) or its title. So
entries that don't have one of those two fields *will not* be completed.
- DOIs are only used if they can be recognized, so the `doi` field should
  contain "10.xxxx/yyyy" or an URL ending with it.
- Titles should be the full title. They are compared excluding case and
  punctuation, but titles with missing words will not match.
- If one or more authors are present, entries with no common authors will not
  match. Authors are compared using lower case last names only. Be sure to use
  one of the correct BibTeX formats for the author field:
  ```bibtex
  author = {First Last and Last, First and First von Last}
  ```
  (see
  [https://www.bibtex.com/f/author-field/](https://www.bibtex.com/f/author-field/)
  for full details)
- If the year is known, entries with different years will also not match.

**Disclaimers:**

- There is no guarantee that the script will find matches for your entries, or
  that the websites will have any data to add to your entries, (or even that the
  website data is correct).

- The script is designed to minimize the chance of false positives - that is
  adding data from another similar-ish entry to your entry. If you find any such
  false positive please report them using the [issue
  tracker](https://github.com/dlesbre/bibtex-autocomplete/issues).

**How are entries completed?**

Once responses from all websites have been found, the script will add fields
by performing a majority vote among the sources. To do so it uses smart
normalization and merging tactics for each field:
- Authors (and editors) match if they have same last names and, if both first
  names present, the first name of one is equal/an abbreviation of the other.
  Author lists match they have at least one author in common.
- ISSN and ISBN are normalized and have their check digits verified. ISBN are converted
  to their 13 digit representation.
- URL and DOI are checked for valid format, and further validated by querying
  them online to ensure they exist. DOI are normalized to strip any leading URL
  and converted to lowercase.
- Many fields match with abbreviation detection (journal, institution, booktitle,
  organization, publisher, school and series). So `ACM` will match
  `Association for Computer Machinery`.
- Pages are normalized to use `--` as separator.
- All other fields are compared excluding case and punctuation.

The script will not overwrite any user given non-empty fields, unless the
`-f/--force-overwrite` flag is given. If you want to check what fields are
added, you can use `-v/--verbose` to have them printed to standard output (with
source information), or `-p/--prefix` to have the new fields be prefixed with
`BTAC` in the output file.

## Installation

Can be installed with [pip](https://pypi.org/project/pip/) :

```console
pip install bibtexautocomplete
```

You should now be able to run the script using either command:

```console
btac --version
python3 -m bibtexautocomplete --version
```

**Note:** `pip` no longer allows installing scripts globally in systems with other
package managers (like most Linux distros). You can install the script locally in
a [virtual environment](https://docs.python.org/3/library/venv.html) or globally
using [pipx](https://pipx.pypa.io/stable/):

```console
sudo apt install pipx
pipx install bibtexautocomplete
```

### Shell tab completion

If you want tab based completion for `btac` in your shell, you must install
the optional [argcomplete](https://pypi.org/project/argcomplete/) dependency.
```bash
# Either install the package separately
pip install argcomplete
# Or as a btac optional dependency
pip install bibtexautocomplete[tab]
```
You then need to register the tab auto-completer. On bash/zsh:
- You can activate completion just for this script with
  ```bash
  eval "$(register-python-argcomplete btac)"
  ```
  For repeated use, I recommend adding this line to your `.bashrc` or `.bash_profile`.
- Alternatively, you can activate completion for all python scripts
  using argcomplete by running
  ```bash
  activate-global-python-argcomplete
  ```
  and then restarting your shell

If using another shell than bash/zsh on Linux or MacOS, support is not guaranteed.
See [github.com/kislyuk/argcomplete/contrib](https://github.com/kislyuk/argcomplete/tree/develop/contrib) for instructions on getting it working on other shells.

### Dependencies

This package has two dependencies (automatically installed by pip) :

- [bibtexparser](https://bibtexparser.readthedocs.io/) (<2.0.0)
- [alive_progress](https://github.com/rsalmei/alive-progress) (>= 3.0.0) for the fancy progress bar

It also has an optional dependency, [argcomplete](https://pypi.org/project/argcomplete/) for tab based completion. It is installed if you `pip install  bibtexautocomplete[tab]`.

## Usage

The command line tool can be used as follows:
```console
btac [--flags] <input_files>
```

**Examples :**

- `btac my/db.bib` : reads from `./my/db.bib`, writes to `./my/db.btac.bib`.
  A different output file can be specified with `-o`.
- `btac -i db.bib` : reads from `db.bib` and overwrites it (inplace flag).
  Avoid on non backed-up/version-controlled files, I'd hate it if my script
  corrupted your data.
- `btac folder` : reads from all files ending with `.bib` in folder. Excludes
  `.btac.bib` files unless they are the only `.bib` files present. Writes to
  `folder/file.btac.bib` unless inplace flag is set.
- `btac` with no inputs is same as `btac .`, reads file from current working directory
- `btac -c doi ...` only completes DOI fields, leave others unchanged
- `btac -v ...` verbose mode, pretty prints all new fields when done.
  See [this image](https://raw.githubusercontent.com/dlesbre/bibtex-autocomplete/master/imgs/btac-verbose.png) for a preview of verbose output.

**Note:** the [parser](https://pypi.org/project/bibtexparser/) doesn't preserve
format information, so this script will reformat your files. Some [formatting
options](#output-formatting) are provided to control output format.

**Slow responses:** Sometimes due to server traffic, a source DB may take significantly longer
to respond and slow `btac`.
- You can increase timeout with `btac ... -t 60` (60s) or `btac ... -t -1` (no timeout)
- You can disable queries to the offender `btac ... -Q <website>`
- You can try again at another time

## Command line arguments

As `btac` has a lot of option I'd recommend setting up an alias if you use a lot
regularly.

### Specifying output

- `-o --output <file.bib>`

  Write output to given file. Can be used multiple times when also giving
  multiple inputs. Maps inputs to outputs in order. If there are extra inputs,
  uses default name (`old_name.btac.bib`). Ignored in inplace (`-i`) mode.

  For example `btac db1.bib db2.bib db3.bib -o out1.bib -o out2.bib` reads `db1.bib`,
  `db2.bib` and `db3.bib`, and write their outputs to `out1.bib`, `out2.bib`
  and `db3.btac.bib` respectively.

- `-i --inplace` Modify input files inplace, ignores any specified output files.
  Avoid on non backed-up/version-controlled files, I'd hate it if my script
  corrupted your data.

- `-O --no-output` don't write any output files (except the one specified by `--dump-data`)
  can be used with `-v/--verbose` mode to only print a list of changes to the terminal

### Query filtering

- `-q --only-query <site>` or `-Q --dont-query <site>`

  Restrict which websites to query from. `<site>` must be one of: `openalex`,
  `crossref`, `arxiv`, `s2`, `unpaywall`, `dblp`, `researchr`, `hep`. These arguments
  can be used multiple times, for example to only query Crossref and DBLP use
  `-q crossref -q dblp` or
  `-Q openalex -Q researchr -Q unpaywall -Q arxiv -Q s2 -Q hep`

- `-e --only-entry <id>` or `-E --exclude-entry <id>`

  Restrict which entries should be autocompleted. `<id>` is the entry ID used in
  your BibTeX file (e.g. `@inproceedings{<id> ... }`). These arguments can also
  be used multiple times to select only/exclude multiple entries

- `--sf --start-from <id>`

  Only complete the entries that come after the given id (inclusive). This is
  useful when resuming a previously interrupted auto-completion on the same file.

- `-c --only-complete <field>` or `-C --dont-complete <field>`

  Restrict which fields you wish to autocomplete. Field is a BibTeX field (e.g.
  `author`, `doi`,...). So if you only wish to add missing DOIs use `-c doi`.

- `-b --filter-fields-by-entrytype <required|optional|all>` only add fields that correspond to
  the given entry type in bibtex's data model. Disabled by default. `required`
  only adds required fields, `optional` adds required and optional fields, and
  `all` adds required, optional and non-standard fields (doi, issn and isbn).
  A list of required/optional fields by entry type can be found
  [on the tex stackexchange](https://tex.stackexchange.com/questions/239042/where-can-we-find-a-list-of-all-available-bibtex-entries-and-the-available-fiel)

- `-w --overwrite <field>` or `-W --dont-overwrite <field>`

  Force overwriting of the selected fields. If using `-W author -W journal`
  your force overwrite of all fields except `author` and `journal`. The
  default is to override nothing (only complete absent and blank fields).

  For a more complex example `btac -C doi -w author` means complete all fields
  save DOI, and only overwrite author fields.

  You can also use the `-f` flag to overwrite everything or the `-p` flag to add
  a prefix to new fields, thus avoiding overwrites.

- `-m --mark` and `-M --ignore-mark`

  This is useful to avoid repeated queries if you want to run `btac` many times
  on the same (large) file.

  By default, `btac` ignores any entry with a `BTACqueried` field. `--ignore-mark`
  overrides this behavior.

  When `--mark` is set, `btac` adds a `BTACqueried = {yyyy-mm-dd}` field to each entry
  it queries.

### New field formatting

You can use the following arguments to control how `btac` formats the new fields
- `--fu --escape-unicode` replace unicode symbols by latex escapes sequence (for
  example: replace `é` with `{\'e}`). The default is to keep unicode symbols as is.
- `--fp --protect-uppercase <field>` or `--FP --dont-protect-uppercase <field>` or
  `--fpa --protect-all-uppercase`, insert braces around words containing uppercase
  letters in the given fields to ensure bibtex will preserve them. The three
  arguments are mutually exclusive, and the first two can be used multiple times
  to select/deselect multiple fields.


### Global output formatting

Unfortunately [bibtexparser](https://pypi.org/project/bibtexparser/) doesn't
preserve format information, so this script will reformat your BibTeX file. Here
are a few options you can use to control the output format:

- `--fa --align-values` pad field names to align all values

  ```bibtex
  @article{Example,
    author = {Someone},
    doi    = {10.xxxx/yyyyy},
  }
  ```

- `--fc --comma-first` use comma first syntax

  ```bibtex
  @article{Example
    , author = {Someone}
    , doi = {10.xxxx/yyyyy}
    ,
  }
  ```

- `--fl --no-trailing-comma` don't add the last trailing comma
- `--fi --indent <space>` space used for indentation, default is a tab.
  Can be specified as a number (number of spaces) or a string with spaces
  and `_`, `t`, and `n` characters to mark space, tabs and newlines.

### Optional flags

- `-p --prefix` Write new fields with a prefix. The script will add `BTACtitle =
  ...` instead of `title = ...` in the bib file. This can be combined with `-f`
  to safely show info for already present fields.

  Note that this can overwrite existing fields starting with `BTACxxxx`, even
  without the `-f` option.
- `-f --force-overwrite` Overwrite already present fields. The default is to
  overwrite a field only if it is empty or absent
- `-D --diff` only print the new fields in the output file. In this mode, old
  fields are removed and entries with no new fields are deleted. This cannot be
  used with the `-i --inplace` flag for safety reasons. If you really want to overwrite
  your input file (and delete a bunch of data in the process), you can do so with
  by specifying it explicitly via the `-o --output` option.
- `-u --copy-doi-to-url` If a DOI is found but no URL, set the URL field
  to `https://dx.doi.org/<doi>`

- `-t --timeout <float>` set timeout on request in seconds, default: 20.0 s,
  increase this if you are getting a lot of timeouts. Set it to -1 for no timeout.
- `-S --ignore-ssl` bypass SSL verification. Use this if you encounter the error:
  ```
  [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1129)
  ```
  Another (better) fix for this is to run `pip install --upgrade certifi` to update python's certificates.
- `--ns --no-skip` disable skipping. By default, btac will skip queries to sources
  if they lag behind (>=10 queries remain or >=60s delay between queries) when
  2/3rds of the other sources have completed. This avoids having a single source
  slow down btac considerably.

- `-d --dump-data <file.json>` writes matching entries to the given JSON files.

  This allows to see duplicate fields from different sources that are otherwise overwritten when merged into a single entry.

  The JSON file will have the following structure:

  ```json
  [
    {
      "entry": "<entry_id>",
      "new-fields": 8,
      "crossref": {
        "query-url": "https://api.crossref.org/...",
        "query-response-time": 0.556,
        "query-response-status": 200,
        "author" : "Lastname, Firstnames and Lastname, Firstnames ...",
        "title" : "super interesting article!",
        "..." : "..."
      },
      "openalex": ...,
      "arxiv": null, // null when no match found
      "unpaywall": ...,
      "dblp": ...,
      "researchr": ...,
      "inspire": ...
    },
    ...
  ]
  ```

- `-v --verbose` verbose mode shows more info. It details entries as they are
  being processed and shows a summary of new fields and their source at the end.
  Using it more than once prints debug info (up to four times).

  Verbose mode looks like this:

  ![verbose-output.png](https://raw.githubusercontent.com/dlesbre/bibtex-autocomplete/master/imgs/btac-verbose.png)
- `-s --silent` hide info and progress bar. Keep showing warnings and errors.
  Use twice to also hide warnings, thrice to also hide errors and four times to
  also hide critical errors, effectively killing all output.
- `--color <auto|always|never>` sets whether btac should use colored output.
  Can also be set by the `NO_COLOR` or the `CLICOLOR_FORCE` environment variables,
  as explained here: http://bixense.com/clicolors/. Defaults to `auto`, which checks
  if standard output is a terminal via the `isatty` function

- `--version` show version number
- `-h --help` show help

## Running from python

You can call the main function of this script from python directly, specifying
a list of arguments as you would on the command line:
```python
from bibtexautocomplete import main

main(["file.bib", "-o", "output.bib"])
```

For more interactivity and more varied inputs/outputs than reading from files and
writing to files, use the `BibtexAutocomplete` class. Here is a small demonstration:
```python
from bibtexautocomplete import BibtexAutocomplete

# 1 - Create a BibtexAutocomplete instance with the desired settings
# Note: some settings are stored in global variables, so avoid having multiple
# instances of this class in parrallel
completer = BibtexAutocomplete(**settings)

# 2 - Load a Bibtex information using any of the following
# 2.1 - Load a single file or list of files
completer.load_file("ex.bib")
completer.load_file(["ex1.bib", "ex2.bib"])
# 2.2 - Load bibtex content as string or list of strings
completer.load_string(bibtex)
completer.load_string([bibtex1, bibtex2])
# 2.3 - Load entry, list of entries, or list of list of entries as a dict
# Lowercase name for fields, "ID" and "ENTRYTYPE" for entry id and type
completer.load_entry({
  "author": "John Doe",
  "title": "My Awesome Paper",
  "ID": "foo",
  "ENTRYTYPE": "article"
})
# You can also specify author and editor fields as a (list of) firstnames and lastnames
completer.load_entry({
  "author": [{"firstname": "John"}, {"lastname": "Doe"}],
  "title": "My Awesome Paper",
  "ID": "foo",
  "ENTRYTYPE": "article"
})

# 3 - Run the completer (may take a while)
completer.autocomplete()

# 4 - Get the results
# As the input may be split into mutliple files (or strings), so is the output
# The length of output list is the sum of:
# - the length of lists passed to load_file and load_string
# - the number of calls to load_entry
# When using write_file, you must provide the same number of filepaths
completer.write_file("ex.btac.bib")
completer.write_file(["ex1.bib", "ex2.bib"])
completer.write_string() # type: list[str]
completer.write_entry() # type: list[list[EntryType]]
```

The settings passed to the `BibtexAutocomplete` constructor mirror the
command-line arguments, see [their documentation](#command-line-arguments) for
details.
```python
lookups: Iterable[LookupType] = ...,
# Specify which entries should be completed (default: all)
entries: Optional[Container[str]] = None,
mark: bool = False,
ignore_mark: bool = False,
prefix: bool = False,
escape_unicode: bool = False,
diff_mode: bool = False,
# Restrict which fields should be completed (default: all)
fields_to_complete: Optional[Set[FieldType]] = None,
# Specify which fields should be overwritten (default: none)
fields_to_overwrite: Optional[Set[FieldType]] = None,
# Specify which fields should have uppercase protection (default: none)
fields_to_protect_uppercase: Container[str] = set(),
filter_by_entrytype: Literal["no", "required", "optional", "all"] = "no",
copy_doi_to_url: bool = False,
start_from: Optional[str] = None,
dont_skip_slow_queries: bool = False,
timeout: Optional[float] = 20,  # Timeout on all queries, in seconds
ignore_ssl: bool = False,  # Bypass SSL verification
verbose: int = 0,  # Verbosity level, from 4 (very verbose debug) to -3 (no output)
# Output formatting
align_values: bool = False,
comma_first: bool = False,
no_trailing_comma: bool = False,
indent: str = "\t",
```


## Credit and license

This project was first inspired by the solution provided by
[thando](https://tex.stackexchange.com/users/182467/thando) in this
[TeX stack exchange post](https://tex.stackexchange.com/questions/6810/automatically-adding-doi-fields-to-a-hand-made-bibliography). I worked on as
part of a course on
[Web data management](https://moodle.r2.enst.fr/moodle/course/view.php?id=142) in
2021-2022 as part of my masters ([MPRI](https://wikimpri.dptinfo.ens-cachan.fr/doku.php)).

This project is free and open-source. It is distributed under terms of the
[MIT License](https://choosealicense.com/licenses/mit/). See the
[LICENSE](https://github.com/dlesbre/bibtex-autocomplete/blob/master/LICENSE)
file for more information
