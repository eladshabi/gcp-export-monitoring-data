# gcp-export-monitoring-data

This project was made to export time series data points from Google Cloud Monitoring and write it to a local JSON new line file with the point parameters Time (datetime) and value (int).

To run the main file, please use the following arguments:

--project - The GCP project id to export the monitoring from.

--filter - The cloud monitoring filter expression. Link to the filter documentation https://cloud.google.com/monitoring/api/v3/filters

--weeks - The number of weeks back to get the metric data, minimum one maximum six.

--days - The number of days back to get the metric data.

--hours - The number of hours back to get the metric data.

--service_account_credentials_path - the local path to the credentials file, if the ENV parameter "GOOGLE_APPLICATION_CREDENTIALS
" was set do not add this argument.

--output_file_name - the JSON output file name that will include the data.

Example:

```
python main.py --project=<PROJECT-ID> \
--weeks=5 \
--days=3 \
--hours=2 \
--filter='metric.type = "pubsub.googleapis.com/topic/send_message_operation_count"' \
--service_account_credentials_path=<CREDETIALS_PATHC> \
--output_file_name=pubsub_monitorig_data

```
