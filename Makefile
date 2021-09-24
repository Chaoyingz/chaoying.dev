default:
	make format

format:
	@echo "Format the code (and imports)."
	poetry run isort ./
	poetry run black ./

lint:
	@echo "Run the linting checks."
	pre-commit run --all-files

dev:
	@echo "Start dev server."
	poetry run uvicorn app.main:app  --reload --debug

test:
	@echo "Run the tests."
	poetry run pytest -rs -p no:warnings

coverage:
	@echo "Get the test coverage (xml and html) with the current version."
	poetry run coverage run -m pytest -rs -p no:warnings
	poetry run coverage report -m
	poetry run coverage xml
	echo "Generated XML report: ./coverage.xml"
	poetry run coverage html
	echo "Generated HTML report: ./htmlcov/index.html"

setup:
	@echo "Configure the development environment."
	pre-commit install
	poetry install
