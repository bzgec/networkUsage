# Setup environment
setup:
	pip install -r requirements.txt


# Check for best code standards
# flake8 --ignore=E501,F401 --max-complexity 10 --exclude .venv,.git,__pycache__ .
check:
	flake8 --ignore=E501 --max-complexity 10 --exclude .venv,.git,__pycache__ .
