# General Parameters #
PROJECT_ID="elad-playground"

# Cloud Function Parameters #
CF_NAME="metric_exporter"
CF_REGION="us-central1"
CF_SA="metric-exporter-cloud-function@"$(PROJECT_ID)".iam.gserviceaccount.com" #monitoring.timeSeries.list (custom role), BigQuery Job User and Data Editor on the Dataset level.
RUNTIME="python37"
SOURCE_PATH="./cloud_function_files" # Source file path for the cloud function
ENTRY_POINT="export" # Don't change
TIMEOUT=540 # In seconds max=540
MEMORY=128 # In MB max=8192MB

# Cloud Scheduler Parameters #
EXPORT_NAME=daily_bucket_object_count
TIME_ZONE="UTC"
SCHEDULE="* * * * *"
WEEKS=0
DAYS=0
HOURS=1
FILTER='metric.type = "storage.googleapis.com/storage/object_count"'
SCHEDULER_SA="scheduler-test@"$(PROJECT_ID)".iam.gserviceaccount.com" # Cloud function invoker
HEADERS="Content-Type=application/json,User-Agent=Google-Cloud-Scheduler"

# BigQuery Parameters #
BQ_DATASET="exporter"
BQ_TABLE="staging_test"
BQ_LOCATION="US"

# System Parameters - Don't change #
MSG_TMP_DIR="./msg_tmp"
MSG_BODY_FILE_NAME="msg.json"


deploy_cloud_function:
	gcloud functions deploy $(CF_NAME) --region=$(CF_REGION) --runtime=$(RUNTIME) --trigger-http --source=$(SOURCE_PATH) \
	--entry-point=$(ENTRY_POINT) --project=$(PROJECT_ID) --service-account=$(CF_SA) \
	--memory=$(MEMORY) --timeout=$(TIMEOUT)

deploy_scheduler: build_json_msg
	gcloud scheduler jobs create http $(EXPORT_NAME) --project=$(PROJECT_ID) --schedule=$(SCHEDULE) \
	--uri="https://"$(CF_REGION)"-"$(PROJECT_ID)".cloudfunctions.net/"$(CF_NAME) --http-method=POST \
	--headers=$(HEADERS) \
	--oidc-service-account-email=$(SCHEDULER_SA) \
	--message-body-from-file=$(MSG_TMP_DIR)"/"$(MSG_BODY_FILE_NAME) \
	--time-zone=$(TIME_ZONE)

build_json_msg:
	python build_message_body.py --project=$(PROJECT_ID) --filter=$(FILTER) --weeks=$(WEEKS) --days=$(DAYS) --hours=$(HOURS) --bq_destination_dataset=$(BQ_DATASET) \
	--bq_destination_table=$(BQ_TABLE) --MSG_TMP_DIR=$(MSG_TMP_DIR) --MSG_BODY_FILE_NAME=$(MSG_BODY_FILE_NAME)

clean:
	rm $(MSG_TMP_DIR)"/"$(MSG_BODY_FILE_NAME)

delete_cloud_function:
	gcloud functions delete $(CF_NAME) --region=$(CF_REGION) --project=$(PROJECT_ID)

delete_scheduler:
	gcloud scheduler jobs delete $(EXPORT_NAME) --project=$(PROJECT_ID)

create_bq_dataset:
	bq --location=$(BQ_LOCATION) mk --dataset $(PROJECT_ID):$(BQ_DATASET)

schedule_metric_export: deploy_scheduler clean

full_build: deploy_cloud_function schedule_metric_export