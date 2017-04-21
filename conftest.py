import json
import pytest
import sys
import datetime

from testrail_api import APIClient


ADD_RESULTS_URL = 'add_results_for_cases/{0}'
ADD_TESTRUN_URL = 'add_run/{0}'

PYTEST_TO_TESTRAIL_STATUS = {
    "passed": 1,
    "failed": 5,
    "skipped": 2,
}

report = {
        'passed':[],
        'skipped':[],
        'failed':[],
        'duration':0.0,
        }

fast_config = {
    "TestRailURL": "",
    "Credentials":{
        "TestRailsUserName": "",
        "TestRailsPassword": "
    },
    "TestRunInformation":{
        "ProjectId": "",
        "SuiteId": ""
    }
}

# setup testrail client before tests

client = APIClient(fast_config['TestRailURL'])
client.user = fast_config['Credentials']['TestRailsUserName']
client.password = fast_config['Credentials']['TestRailsPassword']

def build_dict_from_json_config(file):
    """
    (str) -> (dict)
    Makes a dict of a json config file.
    """
    with open(file, encoding='utf-8') as json_file:
        json_config = json.loads(json_file())

    return json_config


def pytest_addoption(parser):
    """
    Used to initiate
    """
    group = parser.getgroup("report_to_testrail")
    group.addoption("--totestrail",
                action="store",
                help='The json filename to which to dump test results.')

def pytest_runtest_setup(item):
    """
    Records, before every test, the corresponding
    TestRail test case number.
    """
    t_marker = item.get_marker("testrail")
    if t_marker is not None:
        for info in t_marker:
            print("glob args=%s kwargs=%s" %(info.args, info.kwargs))
            sys.stdout.flush()


def pytest_configure(config):
    """
    Register an additional marker in the pytest config.
    """
    config.addinivalue_line("markers",
            "testrail: testcaseid involved with test")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    During every individual test the report is updated.
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        if rep.passed:
            report['passed'].append(get_id_from_marker(item))
        if rep.failed:
            report['failed'].append(get_id_from_marker(item))
    else:
        if rep.skipped:
            report['skipped'].append(rep.nodeid + ":" + get_id_from_marker(item))

    return rep


def get_id_from_marker(item):
    """
    Pulls out test case id from marker.
    """
    markerString = str(item.get_marker('testrail'))
    id = ""
    for char in markerString:
	    if char.isdigit() is True:
		    id = id + char

    return id


def pytest_sessionfinish(session, exitstatus):
    """
    Passes in thes test results to be used in building a test run
    and reporting.
    """
    if report['passed'] or report['failed'] or report['skipped']:

        testRunId = create_test_run(fast_config['TestRunInformation']['ProjectId'],
                        fast_config['TestRunInformation']['SuiteId'],
                        get_test_name(),
                        find_test_cases_used(report))

        report_results(testRunId,compile_results_from_json(report))


def get_test_name():
    """
    Builds a generic test name based on date and time.
    """
    return "Auto Test | {0}".format(str(datetime.datetime.now()))

def report_results(testRunId, results):
    """
    report results to TestRail using client
    """
    data = {'results': results}
    client.send_post(ADD_RESULTS_URL.format(testRunId), data)


def create_test_run(projectId, suiteId, testRunName, testCases):
    """
    Create testrun with ids collected from markers.
    """
    data = {
        'suite_id': suiteId,
        'name': testRunName,
        'include_all': False,
        'case_ids': testCases,
    }

    response = client.send_post(
        ADD_TESTRUN_URL.format(projectId),
        data
    )

    for key, _ in response.items():
        if key == 'error':
            print('Failed to create testrun: {}'.format(response))
        else:
            return response['id']

# TODO : Add skipping here and reorganize
def find_test_cases_used(json_file):
    cases = []
    for case in json_file['passed']:
        cases.append(case)

    for case in json_file['failed']:
        cases.append(case)

    return cases

#TODO: Add in skipped
def compile_results_from_json(obj):
    """
    take json file and read it in order to create
    a list to send to test rail
    """
    results = []

    for test in obj['passed']:
        data = {
            'case_id': test,
            'status_id': 1
        }
        results.append(data)

    for test in obj['failed']:
        data = {
            'case_id': test,
            'status_id': 5
        }
        results.append(data)

    return results

def get_test_outcome(outcome):
    """
    (str) -> (int)
    Converts the given outcome (string from pytest) to
    int for TestRail.
    """
    return PYTEST_TO_TESTRAIL_STATUS[outcome]
