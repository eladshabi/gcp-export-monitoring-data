# gcp-export-monitoring-data

This project was made to export time series data points from Google Cloud Monitoring and write it to a local JSON new line delimited file.

To run the main file, please use the following arguments:

--project - The GCP project id to export the monitoring from.

--filter - The cloud monitoring [filter expression](https://cloud.google.com/monitoring/api/v3/filters).

--weeks - The number of weeks back to get the metric data, minimum one maximum six.

--days - The number of days back to get the metric data.

--hours - The number of hours back to get the metric data.

--mean_series_aligner - Whether to use MEAN aggregation or not.

--alignment_period - Time interval in seconds, that is used to divide the data (use only with mean_series_aligner).

--output_file_name - the JSON output file name that will include the data.

## Authentication

Please see the [offical python gcp authentication document](https://googleapis.dev/python/google-api-core/latest/auth.html) 

## Example:

```
python main.py --project=<PROJECT-ID> \
--weeks=5 \
--days=3 \
--hours=2 \
--filter='metric.type = "pubsub.googleapis.com/topic/send_message_operation_count"' \
--output_file_name=pubsub_monitorig_data
```

## Aggregation Example

```
python main.py --project=<PROJECT-ID> \
--weeks=5 \
--days=3 \
--hours=2 \
--filter='metric.type = "pubsub.googleapis.com/topic/send_message_operation_count"' \
--mean_series_aligner=True \
--alignment_period=120 \
--output_file_name=pubsub_monitorig_data_2_min_agg
```