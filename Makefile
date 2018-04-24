lint:
	docker-compose run --no-deps unrasterize bash -c "flake8 unrasterize"
	docker-compose run --no-deps unrasterize bash -c "pep257 unrasterize"

# Run test suite locally.
test: FORCE
	docker-compose run --no-deps unrasterize pytest -s tests

# Run coverage.
coverage:
	touch data/.coverage
	chmod 777 data/.coverage
	docker-compose run --no-deps unrasterize pytest --cov=unrasterize --cov-config .coveragerc --cov-fail-under=90 --cov-report term-missing

# [Dummy dependency to force a make command to always run.]
FORCE:

