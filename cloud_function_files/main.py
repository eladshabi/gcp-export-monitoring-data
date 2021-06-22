from google.cloud import monitoring_v3
from google.cloud import bigquery
from datetime import timedelta
import argparse
import time
import os
import json


def get_metric_data(project_id, metric_filter, weeks_ago, days_ago, hours_ago, agg, agg_per):
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
    if agg:
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": agg_per},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_MEAN
            }
        )
    else:
        aggregation = None

    print("Sending request to the server...")

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": metric_filter,
            "interval": interval,
            "aggregation": aggregation,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    print("Got response from the server")

    return results


def parse_and_write_as_json_new_line(data, output_file_name, agg):
    print("Parsing the data points")

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
                'double_value': point.value.double_value
            }

            for key, value in metric_name.labels.items():
                dict_point[key] = value

            for key, value in resource_name.labels.items():
                dict_point[key] = value

            points.append(dict_point)

    print(f"Writing the data points into local file {os.getcwd()}/{output_file_name}.json")

    with open(f'/tmp/{output_file_name}.json', 'w') as out_file:
        for data_point in points:
            out_file.write(json.dumps(data_point))
            out_file.write("\n")

    print("Writing operation completed with no errors")

    load_to_bq('elad-playground', 'exporter', output_file_name)


def load_to_bq(project_id, dataset, table_name):
    client = bigquery.Client()

    table_id = f"{project_id}.{dataset}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, autodetect=True,
    )

    table = client.get_table(table_id)
    table_prev_row_number = table.num_rows

    with open(f"/tmp/{table_name}.json", "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    job_res_output = job.result()  # Waits for the job to complete.
    print(f'Job result output:{job_res_output}')

    table = client.get_table(table_id)  # Make an API request.
    print(
        "Loaded {} rows and {} columns to {}".format(
            table.num_rows - table_prev_row_number, len(table.schema), table_id
        )
    )


def hello_world(request):
    request_json = request.get_json()

    print(request_json)

    env_project = request_json['project_id']

    env_filter = request_json['filter']

    env_weeks = request_json['weeks']

    env_days = request_json['days']

    env_hours = request_json['hours']

    env_output_file_name = request_json['output_file_name']

    # env_mean_series_aligner = os.environ.get("--mean_series_aligner")

    # env_alignment_period = os.environ.get("--alignment_period")

    # env_output_file_name = os.environ.get("--output_file_name")

    print(env_filter)

    raw_metrics_data = get_metric_data(env_project, env_filter, int(env_weeks), int(env_days), int(env_hours), None,
                                       None)

    parse_and_write_as_json_new_line(raw_metrics_data, env_output_file_name, None)