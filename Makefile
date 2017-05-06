setup:
	pip install -e .
	pip install -r requirements/dev.txt
	python scraper/install.py

setup_ci:
	pip install -e .
	pip install -r requirements/ci.txt
	python scraper/install.py

ci: test lint typing
	@echo "CI complete"

lint:
	@echo "Running pylint"
	@pylint --rcfile=pylintrc tests justice scraper pylint_custom

test:
	@echo "Running pytest"
	@py.test tests

typing:
	@echo "Running mypy"
	@mypy tests justice scraper pylint_custom --ignore-missing-imports
