all: test

test:
	nosetests --with-doctest --doctest-tests
