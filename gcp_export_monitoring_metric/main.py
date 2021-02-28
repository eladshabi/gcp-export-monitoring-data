from google.cloud import monitoring_v3
from datetime import timedelta
import argparse
import time
import os
import json


def get_metric_data(project_id, metric_filter, weeks_ago, days_ago, hours_ago):
    def get_second_delta(weeks_ago, days_ago, hours_ago):
        return timedelta(weeks=weeks_ago, days=days_ago, hours=hours_ago).total_seconds()

    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    now = time.time()
    time_ago = get_second_delta(weeks_ago, days_ago, hours_ago)

    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval(
        {
            "end_time": {"seconds": seconds, "nanos": nanos},
            "start_time": {"seconds": (seconds - int(time_ago)), "nanos": nanos},
        }
    )

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": f'{metric_filter}',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    return results


def parse_and_write_as_json_new_line(data, output_file_name):
    points = []

    for page in data:
        for point in page.points:
            dict_point = {
                'time': point.interval.start_time.strftime('%d/%m/%Y %H:%M:%S'),
                'value': point.value.int64_value
            }
            points.append(dict_point)

    with open(f'./{output_file_name}.json', 'w') as out_file:
        for data_point in points:
            out_file.write(json.dumps(data_point))
            out_file.write("\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--project", help="GCP Project id", required=True)

    parser.add_argument("--filter", help="Filter string with specific metric", required=True)

    parser.add_argument("--weeks", help="The number of weeks back to get the metric data, minimum 1 maximum 6",
                        required=True, type=int)

    parser.add_argument("--days", help="The number of days back to get the metric data",
                        required=True, type=int)

    parser.add_argument("--hours", help="The number of hours back to get the metric data",
                        required=True, type=int)

    parser.add_argument("--service_account_credentials_path")

    parser.add_argument("--output_file_name", required=True)

    args = parser.parse_args()

    if args.service_account_credentials_path:
        os.environ[
            'GOOGLE_APPLICATION_CREDENTIALS'] = args.service_account_credentials_path

    raw_metrics_data = get_metric_data(args.project, args.filter, args.weeks, args.days, args.hours)

    parse_and_write_as_json_new_line(raw_metrics_data, args.output_file_name)