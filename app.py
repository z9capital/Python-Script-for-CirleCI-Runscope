import requests
import sys
import time
import os


def main():
    trigger_url = sys.argv[1]
    trigger_resp = requests.get(trigger_url)

    if trigger_resp.ok:
        trigger_json = trigger_resp.json().get("data", {})

        test_runs = trigger_json.get("runs", [])

        print "Started {} test runs.".format(len(test_runs))

        results = {}
        while len(results.keys()) < len(test_runs):
            time.sleep(1)

            for run in test_runs:
                test_run_id = run.get("test_run_id")
                if not test_run_id in results:
                    result = _get_result(run)
                    if result.get("result") in ["pass", "fail"]:
                        results[test_run_id] = result

        # pass_count = sum([r.get("result") == "pass" for r in results.values()])
        fail_count = sum([r.get("result") == "fail" for r in results.values()])

        if fail_count > 0:
            # print test_runs[0].get('test_name') + " failed: {} test runs passed. {} test runs failed.".format(pass_count, fail_count)
            print test_runs[0].get('test_name') + " failed: {} test pack runs failed!"
            exit(1)

        print test_runs[0].get('test_name') + " whole test pack are passed!"
    else:
        print "Runscope can not run any test!"
        exit(1)


def _get_result(test_run):
    # generate Personal Access Token at https://www.runscope.com/applications
    if not "RUNSCOPE_ACCESS_TOKEN" in os.environ:
        print "Please set the environment variable RUNSCOPE_ACCESS_TOKEN. You can get an access token by going to https://www.runscope.com/applications"
        exit(1)

    API_TOKEN = os.environ["RUNSCOPE_ACCESS_TOKEN"]

    opts = {
        "base_url": "https://api.runscope.com",
        "bucket_key": test_run.get("bucket_key"),
        "test_id": test_run.get("test_id"),
        "test_run_id": test_run.get("test_run_id")
    }
    result_url = "{base_url}/buckets/{bucket_key}/tests/{test_id}/results/{test_run_id}".format(**opts)
    print "Getting result: {}".format(result_url)

    headers = {
        "Authorization": "Bearer {}".format(API_TOKEN),
        "User-Agent": "python-trigger-sample"
    }
    result_resp = requests.get(result_url, headers=headers)

    if result_resp.ok:
        response_data = result_resp.json().get("data")

        error_variables_data = response_data.get("variables_failed")
        error_assertions_data = response_data.get("assertions_failed")
        error_scripts_data = response_data.get("scripts_failed")

        if (error_variables_data > 0) or (error_assertions_data > 0) or (error_scripts_data > 0):
            requests_array = response_data.get("requests")

            for current_request in requests_array:

                current_error_variables_data = current_request.get("variables_failed")
                current_error_assertions_data = current_request.get("assertions_failed")
                current_error_scripts_data = current_request.get("scripts_failed")

                if (current_error_variables_data > 0) or (current_error_assertions_data > 0) or (current_error_scripts_data > 0):
                    print "* Error with {} method in {}:".format(current_request.get("method"), current_request.get("url"))

                    if current_error_assertions_data > 0:
                        for current_assertion_data in current_request.get("assertions"):
                            print " - {}, actual: {}, target: {}".format(current_assertion_data.get("comparison"),
                                                                         current_assertion_data.get("actual_value"),
                                                                         current_assertion_data.get("target_value"))
                    if current_error_variables_data > 0:
                        print " - Check your Runscope variables"

                    if current_error_scripts_data > 0:
                        print " - Check your Runscope script data"

        return response_data

    return None


if __name__ == '__main__':
    main()
