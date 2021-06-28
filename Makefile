# General Parameters #
PROJECT_ID=<PROJECT-ID>

# Cloud Function Parameters #
CF_NAME="metric_exporter" # Don't change
CF_REGION="us-central1"
CF_SA="metric-exporter-cf-sa@"$(PROJECT_ID)".iam.gserviceaccount.com" # Don't change | monitoring.timeSeries.list (custom role), BigQuery Job User and Data Editor on the Dataset level.
RUNTIME="python37" # Don't change
SOURCE_PATH="./cloud_function_files" # Don't change | Source file path for the cloud function
ENTRY_POINT="export" # Don't change
TIMEOUT=540 # In seconds max=540
MEMORY=128 # In MB max=8192MB

# Cloud Scheduler Parameters #
EXPORT_NAME=<EXPORT-NAME> # Keep this name unique for each metric export, this is the scheduler name as well as the table name in BigQuery
TIME_ZONE="UTC"
SCHEDULE="* * * * *" # Change by your requirements
WEEKS=0
DAYS=0
HOURS=1
FILTER='metric.type = "storage.googleapis.com/storage/object_count"' # Change to your metric filter
SCHEDULER_SA="metric-exporter-scheduler-sa@"$(PROJECT_ID)".iam.gserviceaccount.com" # Don't change Cloud | function invoker
HEADERS="Content-Type=application/json,User-Agent=Google-Cloud-Scheduler" # Don't change

# BigQuery Parameters #
BQ_DATASET=<DATASET-NAME> # Configure only at the first deployment
BQ_TABLE=$(EXPORT_NAME)
BQ_LOCATION="US" #Configure only at the first deployment

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

get_cf_sa_name:
	@echo $(CF_SA)

get_scheduler_sa_name:
	@echo $(SCHEDULER_SA)

schedule_metric_export: deploy_scheduler clean

full_build: deploy_cloud_function schedule_metric_export