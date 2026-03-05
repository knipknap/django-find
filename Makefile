NAME=django_find

###################################################################
# Standard targets.
###################################################################
.PHONY : clean
clean:
	find . -name "*.pyc" -o -name "*.pyo" | xargs -n1 rm -f
	rm -Rf build dist *.egg-info .nox htmlcov .coverage

.PHONY : tests
tests:
	DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/ --verbosity=2

.PHONY : test-matrix
test-matrix:
	uvx nox

.PHONY : coverage
coverage:
	uvx nox -s coverage

###################################################################
# Package builders.
###################################################################
.PHONY : build
build: clean
	uvx --from build pyproject-build --installer uv

.PHONY : publish
publish: build
	uvx twine upload dist/*
