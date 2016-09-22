There are a number of API tests in ws-tests. They depend on code in the
[germinator](https://github.com/OpenTreeOfLife/germinator) repo.

To run a single test from this repo:

    $ cd ws-tests
    $ PYTHONPATH=<germinator>/ws-tests python test_v3_studies_properties.py

where `germinator` = path to germinator repo. Alternatively, you can create
a symbolic link to the `opentreetesting.py` in the ws-tests directory and then
run without the PYTHONPATH business, e.g.:

    $ ln -s <germinator>/ws-tests/opentreetesting.py opentreetesting.py
    $ python test_v3_studies_properties.py

To run all of the tests, use `run_tests.sh` in germinator:

    $ cd <germinator>/ws-tests
    $ ./run_tests.sh -t <otindex_test_dir> <hostname>

where `germinator` = path to germinator repo; `otindex_test_dir` is the path
to the `ws-tests` directory in this repo (otindex); and <hostname> is the host
where otindex is running (http://0.0.0.0:6543 if running locally).

You can change the verbosity of the test output by setting the `VERBOSE_TESTING` environment variable (default = 0; more output = 1; lots of output = 2):

    $ export VERBOSE_TESTING=2
