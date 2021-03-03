from google.cloud import monitoring_v3
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
                "alignment_period": {"seconds": agg_per},  # 20 minutes
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
            }
        )
    else:
        aggregation = None

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": f'{metric_filter}',
            "interval": interval,
            "aggregation": aggregation,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    return results


def parse_and_write_as_json_new_line(data, output_file_name, agg):

    points = []
    for page in data:
        metric_name = page.metric
        resource_name = page.resource

        for point in page.points:

            dict_point = {
                'time': point.interval.start_time.strftime('%d/%m/%Y %H:%M:%S'),
                'metric_type': metric_name.type,
                'resource_type': resource_name.type,
               # 'value': point.value.int64_value
            }

            if agg:
                dict_point['value'] = point.value.double_value
            else:
                dict_point['value'] = point.value.int64_value

            for key, value in metric_name.labels.items():
                dict_point[key] = value

            for key, value in resource_name.labels.items():
                dict_point[key] = value

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

    parser.add_argument("--mean_series_aligner", help='Whether to use MEAN aggregation or not', type=bool)

    parser.add_argument("--alignment_period", help="Time interval in seconds, that is used to divide the data "
                                                   "(use only with mean_series_aligner)", type=int)

    parser.add_argument("--output_file_name", required=True)

    args = parser.parse_args()

    if (args.mean_series_aligner and not args.alignment_period) or\
            (not args.mean_series_aligner and args.alignment_period):
        parser.error('To use aggregation please specify both,  mean_series_aligner and alignment_period.')

    raw_metrics_data = get_metric_data(args.project, args.filter, args.weeks, args.days, args.hours,
                                       args.mean_series_aligner, args.alignment_period)

    parse_and_write_as_json_new_line(raw_metrics_data, args.output_file_name, args.mean_series_aligner)
