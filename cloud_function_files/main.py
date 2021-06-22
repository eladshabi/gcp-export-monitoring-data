from google.cloud import monitoring_v3
from google.cloud import bigquery
from datetime import timedelta
import time
import os
import json


def get_metric_data(project_id, metric_filter, weeks_ago, days_ago, hours_ago):

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

    print("Sending request to the server...")

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": metric_filter,
            "interval": interval,
            "aggregation": None,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    print("Got response from the server")

    return results


def get_second_delta(weeks, days, hours):
    return timedelta(weeks=weeks, days=days, hours=hours).total_seconds()


def parse_and_write_as_json_new_line(project_id, bq_dataset, bq_table, data):

    print("Parsing response into data points")

    points = []
    for page in data:
        metric_name = page.metric
        resource_name = page.resource

        for point in page.points:

            dict_point = {
                'time': point.interval.start_time.strftime('%d/%m/%Y %H:%M:%S'),
                'metric_type': metric_name.type,
                'resource_type': resource_name.type,
                'int_value': point.value.int64_value,
                'double_value': point.value.double_value,
                'string_value': point.value.string_value,
                'bool_value': point.value.bool_value
            }

            for key, value in metric_name.labels.items():
                dict_point[key] = value

            for key, value in resource_name.labels.items():
                dict_point[key] = value

            points.append(dict_point)

    print(f"Writing data points to disk as NEWLINE DELIMITED JSON: {os.getcwd()}/{bq_table}.json")

    with open(f'/tmp/{bq_table}.json', 'w') as out_file:
        for data_point in points:
            out_file.write(json.dumps(data_point))
            out_file.write("\n")

    print("Writing operation completed with no errors")

    load_to_bq(project_id, bq_dataset, bq_table)


def load_to_bq(project_id, dataset, table_name):
    client = bigquery.Client()

    print(f"BigQuery load destination: {project_id}:{dataset}.{table_name}")

    table_id = f"{project_id}.{dataset}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, autodetect=True,
    )

    with open(f"/tmp/{table_name}.json", "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    job.result()  # Waits for the job to complete.

    table = client.get_table(table_id)  # Make an API request.
    print(
        "Load job completed, total rows number is {} and with {} columns on {}".format(
            table.num_rows, len(table.schema), table_id
        )
    )


def export(request):
    request_json = request.get_json()

    print(f'Request content:{request_json}')

    env_project = request_json['project_id']

    env_filter = request_json['filter']

    env_weeks = int(request_json['weeks'])

    env_days = int(request_json['days'])

    env_hours = int(request_json['hours'])

    env_bq_destination_dataset = request_json['bq_destination_dataset']

    env_bq_destination_table = request_json['bq_destination_table']

    print(f"Metric filter: {env_filter}")

    raw_metrics_data = get_metric_data(env_project, env_filter, env_weeks, env_days, env_hours)

    parse_and_write_as_json_new_line(env_project, env_bq_destination_dataset, env_bq_destination_table, raw_metrics_data)