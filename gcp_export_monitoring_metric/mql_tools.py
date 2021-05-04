import subprocess
import requests

token = subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            text=True,
        ).rstrip()

query="fetch gcs_bucket | metric 'storage.googleapis.com/storage/object_count' | group_by 1m, [value_object_count_mean: mean(value.object_count)]| every 1m | within 6h"


q = f'{{"query": "{query}"}}'

headers = {"Content-Type": "application/json",
           "Authorization": f"Bearer {token}"}
res = requests.post("https://monitoring.googleapis.com/v3/projects/elad-playground/timeSeries:query", data=q, headers=headers).json()

print(res)