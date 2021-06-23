# gcp-export-monitoring-data

This project created to export time series data points from Google Cloud Monitoring and load it into Bigquery table.

To do: Add architecture of the project (Scheduler > Cloud Function > BQ)

In order to deploy the pipeline there are configuration parameters on the Makefile:

PROJECT_ID - GCP project id.

CF_REGION - GCP region for deploying the Cloud Function.

CF_SA - Cloud Function service account name.

RUNTIME - The Cloud function python run time version. 

SOURCE_PATH - Local path to the source code of the Cloud Function (Don't change).

ENTRY_POINT - The function name to run (Don't change).

TIMEOUT - Cloud Function timeout (MAX=540).

MEMORY - Cloud Function memory in MB (MAX=8192MB).

EXPORT_NAME - Cloud Scheduler job name for specific export.

TIME_ZONE - Time zone of the Cloud Scheduler.

SCHEDULE - Cron expression for triggering the export [doc](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules).

WEEKS - The number of weeks back to get the metric data for each runtime.

DAYS - The number of days back to get the metric data for each runtime.

HOURS - The number of hours back to get the metric data for each runtime.

FILTER - The cloud monitoring [filter expression](https://cloud.google.com/monitoring/api/v3/filters), keep the pattern of single quote (') on the outer part of the filter and double quote (") inside the filter. Example: FILTER='metric.type = "storage.googleapis.com/storage/object_count"'

SCHEDULER_SA - Cloud Scheduler service account name.

HEADERS - Headers to send for the Cloud Function. (Don't change).

BQ_DATASET - BigQuery dataset name.

BQ_TABLE - BigQuery table name.

BQ_LOCATION - BigQuery dataset location.

MSG_TMP_DIR - internal directory path for temporary files (Don't change). 

MSG_BODY_FILE_NAME - internal temporary file name (Don't change).

Before starting to configure the pipeline we will need to create BigQuery dataset and, 2 dedicated service account that will make use for the Cloud Function, and the Cloud Scheduler:

AS first step, please make sure you authenticated with your user using the gcloud SDK [link](https://cloud.google.com/sdk/gcloud/reference/auth/login) (please make sure you have permissions to create BigQuery Datasets, Cloud Functions and Cloud Scheduler)

##Create BigQuery Dataset:

On the Makefile please fill the parameter BQ_LOCATION, PROJECT_ID, BQ_DATASET and run the following command: make create_bq_dataset.

##Cloud Function service account:

The cloud function will preform an API call to GCP Monitoring service and load data into BigQuery table, for that, we will create a custom role to follow GCP security recommendation of least privilege access including the "monitoring.timeSeries.list" (custom role), BigQuery Job User and Data Editor on the Dataset level.

Please run the following command to create custom role with the monitoring.timeSeries.list permission:
```
gcloud iam roles create metric_exporter_cf_monitoring_api_role --project=<PROJECT-ID> \
  --title=metric_exporter_cf_monitoring_api_role --description="Role for Monitoring API timeSeries.list" \
  --permissions=monitoring.timeSeries.list --stage=GA
```

Create the Cloud Function service account:

```
gcloud iam service-accounts create metric-exporter-cf-sa \
    --description="Cloud Function metric exporter service account" \
    --display-name="Cloud Functio metric exporter service account"
```
The name of the service account is: metric-exporter-cf-sa@<PROJECT-ID>.iam.gserviceaccount.com
```
gcloud projects add-iam-policy-binding <PROJECT-ID> \
    --member="serviceAccount:metric-exporter-cf-sa@<PROJECT-ID>.iam.gserviceaccount.com" \
    --role="projects/<PROJECT-ID>/roles/metric_exporter_cf_monitoring_api_role"
```

```
gcloud projects add-iam-policy-binding <PROJECT-ID> \
    --member="serviceAccount:metric-exporter-cf-sa@<PROJECT-ID>.iam.gserviceaccount.com" \
    --role="roles/bigquery.user"
```

The last permission for the Cloud Function service account is the Data Editor on the Dataset level, please follow the instruction from the [GCP documentation](https://cloud.google.com/bigquery/docs/dataset-access-controls#granting_access_to_a_dataset) and grant to the Cloud function service account the Data Editor on your BigQuery Dataset.

## Cloud Scheduler Service account 
Create the Cloud Scheduler service account:

```
gcloud iam service-accounts create metric-exporter-scheduler-sa \
    --description="Cloud Scheduler metric exporter service account" \
    --display-name="Cloud Scheduler metric exporter service account"
```

Grant to the scheduler service account the "Cloud function invoker" role:

```
gcloud projects add-iam-policy-binding <PROJECT-ID> \
    --member="serviceAccount:metric-exporter-scheduler-sa@<PROJECT-ID>.iam.gserviceaccount.com" \
    --role="roles/cloudfunctions.invoker"
```

TO DO - finish the readme...