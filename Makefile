# https://stackoverflow.com/a/46188210/14246508
# https://stackoverflow.com/a/59335943/14246508
# https://medium.com/stack-me-up/using-makefiles-the-right-way-a82091286950

VENV_DIR_DEV?=.venv.dev
REQUIREMENTS_DEV:=requirements.dev.txt


# Check code for best standards
# flake8 --ignore=E501,F401 --max-complexity 10 --exclude .venv,.git,__pycache__ .
check: venv_dev
	@echo Checking code standards...
	@( \
		source $(VENV_DIR_DEV)/bin/activate; \
		flake8 --ignore=E501 --max-complexity 10 --exclude $(VENV_DIR_DEV),.git,__pycache__ .; \
	)


venv_dev: $(VENV_DIR_DEV)/touchfile


# Create .venv if it doesn't exist - `test -d .venv.dev || python -m venv .venv.dev`
# Activate venv and install requirements inside - `source .venv/bin/activate && pip install -r requirements.txt
# Create `.venv/touchfile` so that this is ran only if requirements file changes
$(VENV_DIR_DEV)/touchfile: $(REQUIREMENTS_DEV)
	test -d $(VENV_DIR_DEV) || python -m venv $(VENV_DIR_DEV)
	source $(VENV_DIR_DEV)/bin/activate && pip install -r $(REQUIREMENTS_DEV)
	touch $(VENV_DIR_DEV)/touchfile
