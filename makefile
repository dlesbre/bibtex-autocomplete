# See 'make help' for a list of useful targets

# ==================================================
# Constants
# ===================================================

PYTHON := python3
PIP := $(PYTHON) -m pip

PRECOMMIT = pre-commit
MYPY = mypy


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
	color_reset  = \033[38;22m
endif

define print
	@echo "$(color_yellow)$(1)$(color_reset)"
endef

# =================================================
# Default target
# =================================================

default: mypy

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
test: ## Tests all the apps with django's tests
	$(call print,No Tests setup)

.PHONY: mypy
mypy: ## Typecheck all file
	$(call print,Running mypy)
	$(MYPY) ./src/ --exclude /migrations/

preprod: test static ## Prepare and check production
	$(PYTHON) $(MANAGER) check --deploy

# =================================================
# Installation
# =================================================

.PHONY: install install-devel setup setup-devel

.PHONY: setup
setup: $(SETTINGS) ## Install dependencies
	$(call print,Installing dependencies)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: setup-dev
setup-dev: $(SETTINGS) ## Install development dependencies
	$(call print,Installing development dependencies)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(call print,Setting up pre-commit)
	$(PRECOMMIT) install
