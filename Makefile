# General Parameter #
PROJECT-ID="elad-playground"
REGION="us-central1"

# Cloud Function Parameters #
Cloud-Function-Name="metric_exporter"
Cloud_Function-Service-Account="metric-exporter-cloud-function@elad-playground.iam.gserviceaccount.com" #monitoring.timeSeries.list (custom role), BigQuery Job User and Data Editor on the Dataset level.
Runtime="python37"
Source="./cloud_function_files" # Source file path for the cloud function
Entry-Point=hello_world # Change it...

# Cloud Scheduler Parameters #
EXPORT-NAME=daily_bucket_object_count
TIME-ZONE="UTC"
Schedule="* * * * *"
WEEKS=0
DAYS=0
HOURS=1
FILTER='metric.type = "storage.googleapis.com/storage/object_count"'
SCHEDULER-SERVICE-ACCOUNT="scheduler-test@elad-playground.iam.gserviceaccount.com" # Cloud function invoker
Headers="Content-Type=application/json,User-Agent=Google-Cloud-Scheduler"

# BigQuery Parameters #
BQ-DEST-TABLE=e2e-test-makefile

# System parameters - Don't change #
MSG_TMP_DIR="./msg_tmp"
MSG_BODY_FILE_NAME="msg.json"


deploy_cloud_function:
	gcloud functions deploy $(Cloud-Function-Name) --region=$(REGION) --runtime=$(Runtime) --trigger-http --source=$(Source) \
	--entry-point=$(Entry-Point) --project=$(PROJECT-ID) --service-account=$(Cloud_Function-Service-Account)

schedule-metric-export: build_json_msg
	gcloud scheduler jobs create http $(EXPORT-NAME) --project=$(PROJECT-ID) --schedule=$(Schedule) \
	--uri="https://"$(REGION)"-"$(PROJECT-ID)".cloudfunctions.net/"$(Cloud-Function-Name) --http-method=POST \
	--headers=$(Headers) \
	--oidc-service-account-email=$(SCHEDULER-SERVICE-ACCOUNT) \
	--message-body-from-file=$(MSG_TMP_DIR)"/"$(MSG_BODY_FILE_NAME) \
	--time-zone=$(TIME-ZONE)

build_json_msg:
	python build_message_body.py --project=$(PROJECT-ID) --filter=$(FILTER) --weeks=$(WEEKS) --days=$(DAYS) --hours=$(HOURS) --output_file_name=$(BQ-DEST-TABLE)

clean:
	rm $(MSG_TMP_DIR)"/"$(MSG_BODY_FILE_NAME)

full_build_test: deploy_cloud_function schedule-metric-export clean

full_delete:
	gcloud scheduler jobs delete $(EXPORT-NAME) --project=$(PROJECT-ID)
	gcloud functions delete $(Cloud-Function-Name) --region=$(REGION) --project=$(PROJECT-ID)

delete_cloud_function:
	gcloud functions delete $(Cloud-Function-Name) --region=$(REGION) --project=$(PROJECT-ID)

delete_scheduler:
	gcloud scheduler jobs delete $(EXPORT-NAME) --project=$(PROJECT-ID)

#TO DO - Complete the Cloud function creation, add clean and document all.