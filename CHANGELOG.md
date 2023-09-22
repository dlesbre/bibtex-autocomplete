# Change Log

## Version ??? - Not yet released

- Add year check to match algorithm, entry with different year will not match


## Version 1.2.1 - 2023-05-12

- Add `-w --overwrite` and `-W --dont-overwrite` flags
- Fix flag `-f` being ignored in query pre-condition checks, leading
  to skipping queries even if new data could be obtained.
## Version 1.2.0 - 2023-04-14

- Add semantic scholar lookup
- Add `--mark` and `--ignore-mark` option and behavior
- Allow using `-q --only-query` to change lookup order
- Remove DBLP author disambiguation numbers (DBLP would sometimes return `John
  Doe 0002`, which you don't want in your file)
- Fix rejection of some valid DOIs on URL check
- A few under the hood improvements and code cleanup

## Version 1.1.8 - 2023-02-27

- Add global exception catches to resume work if a single lookup fails
- Fix websites returning invalid URLs leading to errors (issue #8, part 2)

## Version 1.1.7 - 2023-02-27

- Fix trying to decode non-text doi response (issue #8)
- Add entry name to error/warning messages

## Version 1.1.6 - 2023-01-06

- Allow for infinite timeout with `-t -1`
- Increase default timeout to 20s as crossref consistently times out
- Add per DB progress meters below the progress bar

## Version 1.1.5 - 2022-09-21

- Fix `btac` script not installing due to bad setup.py options (#6)

## Version 1.1.4 - 2022-09-16

- Add `-p / --prefix` flag
- Add filtered down counter (with `-e` and `-E` options) to output
- Add warning for IDs given with `-e` and `-E` that don't appear in output
- Fix a bug when making output names for multiple files from a directory
- Fix script not installing on Windows CMD (#6)

## Version 1.1.3 - 2022-08-13

- Autodetect files in directories: now `btac folder/` will autocomplete all bib
  files in the given folder, excluding `.btac.bib` files unless they are the
  only files present
- `btac` with no arguments is now same as `btac .`
- Better indent option `--fi / --indent`, now supports using a number of
  specifying with `_`, `n` and `t` for easier console input.
- Added a hint for timeout warnings
- Clarified some things in README

## Version 1.1.2 - 2022-06-11

- Add common authors check when matching entries: if your entries has some
  author field then entries will no common authors will be ignored and entries
  with common authors will be boosted (#5)
- Add sanity check for found URLs and DOIs, `btac` now queries them and follows
  a few redirections to check they resolve to an existing page (#5)
- Some prettier messages and resolve hints for connection errors
- Add `-S/--ignore-ssl` flag (#4)
- Add some logic to dispatch crossref's `container-title` and unpaywall's
  `journal-title` between `journal` and `booktitle` fields.

## Version 1.1.1 - 2022-05-27

- Fix decoding error when opening utf-8 files on Windows (#3)
- Add extra fields `query-url`, `query-response-time` and `query-status` to data
  dumps file
- Added github actions

## Version 1.1.0 - 2022-05-21

- Now also queries arxiv
- Normalize title before querying, should improve matches for title with special
  characters
- Added `--dump-data` option

## Version 1.0.5 - 2022-04-13

- Fixed a bug which prevented installation on python 3.8 (#2)
- Dropped python 3.7 support (It didn't work anyway...)

## Version 1.0.4 - 2022-03-31

- Fixed failed output write in inplace mode
- Fixed double warning for extra output in inplace mode
- Fix default output names ignoring parent directory

## Version 1.0.3 - 2022-03-30

- Clarify new field source priorities
- Fixed unpaywall setting unknown months to 1
- Switch to strict mypy type checking
- Unsupport python 3.6 as alive-progress dropped it
- Switch back to custom logger

## Version 1.0.2 - 2022-03-21

- Fixed missing submodules in upload (#1)
- Removed color from progress bar to avoid issues
- Fixed color not being reset on some terminals
- Added wheel for real this time
- Switch to root logger to avoid custom dependency (temporary, until
  alive-progress is fixed)
- Rewrote README with more detail on options

## Version 1.0.1 - 2022-03-19

- Add direct url to svg so that it can show up on PyPi

## Version 1.0.0 - 2022-03-19

- Multi-threading requests (one thread per website) vastly improves performance
- Overhauled display log: now with colors and pretty sections
- Added query rate limiter to respect politeness requests
- Print summary of changes in verbose mode
- Stopped writing to stdout -> writes to my_file.btac.bib by default now
- ~~Added wheel distribution~~ upload failed
- Fixed a bug when setting fields with no data
- Fixed a bug with ignored command line arguments

## Version 0.4.0 - 2022-03-16

- Initial version of the script
