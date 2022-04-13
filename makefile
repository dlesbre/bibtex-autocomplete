# See 'make help' for a list of useful targets

# ==================================================
# Constants
# ===================================================

PYTHON := python3
PIP := $(PYTHON) -m pip

DIR = .

DOCKER = sudo docker
DOCKER_IMG_NAME = btac

PRECOMMIT = pre-commit
MYPY = mypy
PYTEST = pytest

# set to ON/OFF to toggle ANSI escape sequences
COLOR = ON

# Uncomment to show commands
# VERBOSE = TRUE

# padding for help on targets
# should be > than the longest target
HELP_PADDING = 15

# ==================================================
# Make code and variable setting
# ==================================================

ifeq ($(COLOR),ON)
	color_yellow = \033[93;1m
	color_orange = \033[33m
	color_red    = \033[31m
	color_green  = \033[32m
	color_blue   = \033[34;1m
	color_reset  = \033[0m
endif

define print
	@echo "$(color_yellow)$(1)$(color_reset)"
endef

# =================================================
# Default target
# =================================================

default: mypy
.PHONY: default

# =================================================
# Special Targets
# =================================================

# No display of executed commands.
$(VERBOSE).SILENT:

.PHONY: help
help: ## Show this help
	@echo "$(color_yellow)make:$(color_reset) list of useful targets :"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(color_blue)%-$(HELP_PADDING)s$(color_reset) %s\n", $$1, $$2}'

.PHONY: precommit
precommit: ## run precommit
	$(call print,Running precommit)
	$(PRECOMMIT) run

.PHONY: precommit-all
precommit-all: ## run precommit on all files
	$(call print,Running precommit on all files)
	$(PRECOMMIT) run --all-files

.PHONY: test
test: ## Run all tests
	$(call print,Running pytest)
	$(PYTEST)

.PHONY: mypy
mypy: ## Typecheck all files
	$(call print,Running mypy)
	$(MYPY) --strict ./bibtexautocomplete/ ./tests ./setup.py

.PHONY: flake8
flake8: ## Run flake8 on all files
	$(call print,Running flake8)
	find bibtexautocomplete -type f -name "*.py" -exec flake8 {} ';'
	find tests -type f -name "*.py" -exec flake8 {} ';'

.PHONY: format
format:
	$(call print,Running black)
	black ./bibtexautocomplete/ ./tests/
	$(call print,Running isort)
	isort ./bibtexautocomplete/ ./tests/

# =================================================
# Installation
# =================================================

.PHONY: setup
setup: ## Install dependencies
	$(call print,Upgrading pip)
	$(PIP) install --upgrade pip
	$(call print,Installing package and dependencies)
	$(PIP) install $(DIR)

.PHONY: setup-dev
setup-dev: ## Install development dependencies
	$(call print,Upgrading pip)
	$(PIP) install --upgrade pip
	$(call print,Installing package and development dependencies)
	$(PIP) install -e $(DIR)[dev]
	$(call print,Setting up pre-commit)
	$(PRECOMMIT) install

.PHONY: clean
clean: ## Remove package
	$(call print,Removing package)
	rm -rf build bibtexautocomplete.egg-info

.PHONY: clean-all
clean-all: ## Remove package and venv
	$(call print,Removing package and dependencies and virtual environment)
	rm -rf build bibtexautocomplete.egg-info
	rm -rf venv

.PHONY: deploy
deploy: ## Build and deploys the package
	$(call print,Removing previous dist)
	rm -rf dist/*
	$(call print,Building package)
	$(PYTHON) setup.py sdist bdist_wheel
	$(call print,Deploying package)
	twine upload dist/*

# =================================================
# Docker
# =================================================

.PHONY: docker-build
docker-build: ## Build the docker image
	$(call print,Building docker image)
	$(DOCKER) build -t $(DOCKER_IMG_NAME) .

.PHONY: docker-run
docker-run: ## Run the docker image (requires building first)
	$(call print,Running docker image)
	$(DOCKER) run --rm -it $(DOCKER_IMG_NAME)
