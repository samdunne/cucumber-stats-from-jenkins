import itertools
import json
import urllib
from collections import defaultdict


def gather_jobs(job_name):
    url = "http://hudson/job/%s/api/json" % job_name
    return json.load(urllib.urlopen(url))


def fetch_report_for_build(job_name, build):
    url = "http://hudson/job/%s/%s/testReport/api/json" % (job_name, build)
    return json.load(urllib.urlopen(url))


def cases_for_build_report(report):
    raw_cases = [c['cases'] for c in report['suites']]
    return list(itertools.chain.from_iterable(raw_cases))


def group_tests_by_status(cases):
    return [(t['name'], t['status']) for t in cases]


def extract_group_for_build(b):
    report = fetch_report_for_build(b)
    cases = cases_for_build_report(report)
    return group_tests_by_status(cases)


def mapper(tests):
    '''
    Expects to be called with a list of grouped tests

    >>> tests = [('foo', 'PASSED'), ('foo', 'FAILED'), ('bar', 'PASSED')]
    >>> mapper(tests)
    {'foo': {'FAILED': 1, 'PASSED': 1}, 'bar': {'PASSED': 1}}
    '''
    mapped_tests = {}
    tests.sort()
    for key, group in itertools.groupby(tests, lambda x: x[0]):
        d = defaultdict(int)
        for test in group:
            d[test[1]] += 1
        mapped_tests[key] = dict(d)
    return mapped_tests


def dump_results(results):
    for r in results:
        print "%s\t%s" % r

if __name__ == '__main__':
    all_dev_cucumber_jobs = gather_jobs('dev-cucumber')
    builds = [b['number'] for b in all_dev_cucumber_jobs['builds']]
    for b in builds:
        try:
            report = fetch_report_for_build('dev-cucumber', b)
            cases = cases_for_build_report(report)
            results = group_tests_by_status(cases)
            dump_results(results)
        except ValueError:
            pass
