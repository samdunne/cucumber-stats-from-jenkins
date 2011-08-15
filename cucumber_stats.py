import sys
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


def compute_success_rate(result_dict):
    '''
    Computes the success rate for a given test result

    >>> t = {'FAILED':30,'PASSED':60,'FIXED':10,'REGRESSION':5}
    >>> compute_success_rate(t)
    0.66666666666666663
    >>> t = {'FAILED':30}
    >>> compute_success_rate(t)
    0.0
    '''
    fails = result_dict.get('FAILED', 0) + result_dict.get('REGRESSION', 0)
    passes = result_dict.get('FIXED', 0) + result_dict.get('PASSED', 0)
    total = fails + passes
    try:
        return passes / float(total)
    except ZeroDivisionError, e:
        return 0.0
    

def dump_results(results):
    for k,v in results.items():
        print "%s\t%s\t%s" % (compute_success_rate(v), k, v)


def flatten(list_of_lists):
    return sum(list_of_lists, [])


def truncate_build_list(start_at, l):
    '''

    >>> l = [1,2,3,4,5,6,7,8,9]
    >>> truncate_build_list(5, l)
    [5, 6, 7, 8, 9]
    '''
    start_at_index = l.index(start_at)
    return l[start_at_index:]


if __name__ == '__main__':
    all_dev_cucumber_jobs = gather_jobs('dev-cucumber')
    builds = [b['number'] for b in all_dev_cucumber_jobs['builds']]
    builds.sort()
    results = []
    if len(sys.argv) >= 1:
        start_at = int(sys.argv[1])
        builds = truncate_build_list(start_at, builds)
    for b in builds:
        try:
            report = fetch_report_for_build('dev-cucumber', b)
            cases = cases_for_build_report(report)
            results.append(group_tests_by_status(cases))
        except ValueError:
            pass
    dump_results(mapper(flatten(results)))
