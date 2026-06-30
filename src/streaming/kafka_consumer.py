# """
# Kafka consumer — subscribes to `absence-events`, scores each record with
# the same AbsenteeismModel class the FastAPI service uses, and writes
# results to the `absenteeism_predictions` BigQuery table.
# """

# import json
# import os
# import sys
# from datetime import datetime, timezone

# from kafka import KafkaConsumer
# from google.cloud import bigquery

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from model.absenteeism_model import AbsenteeismModel
# from preprocessing.feature_config import FEATURE_COLUMNS

# TOPIC = "absence-events"
# BOOTSTRAP_SERVERS = "localhost:9092"
# GROUP_ID = "absenteeism-scoring-consumer"

# PROJECT_ID = "absenteeism-risk-platform"
# DATASET = "absenteeism_analytics"
# PREDICTIONS_TABLE = f"{PROJECT_ID}.{DATASET}.absenteeism_predictions"

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
# SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")


# def main():
#     scorer = AbsenteeismModel(model_path=MODEL_PATH, scaler_path=SCALER_PATH)
#     bq_client = bigquery.Client(project=PROJECT_ID)

#     consumer = KafkaConsumer(
#         TOPIC,
#         bootstrap_servers=BOOTSTRAP_SERVERS,
#         group_id=GROUP_ID,
#         auto_offset_reset="earliest",
#         value_deserializer=lambda v: json.loads(v.decode("utf-8")),
#     )

#     print(f"Listening on topic '{TOPIC}' at {BOOTSTRAP_SERVERS}, "
#           f"writing scored results to {PREDICTIONS_TABLE} ...")

#     for message in consumer:
#         event = message.value
#         record_id = event.get("record_id")

#         features = {col: event[col] for col in FEATURE_COLUMNS}
#         result = scorer.predict_single(features)

#         row = {
#             "record_id": record_id,
#             "scored_at": datetime.now(timezone.utc).isoformat(),
#             "excessive_absenteeism_risk": result["excessive_absenteeism_risk"],
#             "risk_probability": result["risk_probability"],
#             "source": "streaming",
#             **features,
#         }

#         errors = bq_client.insert_rows_json(PREDICTIONS_TABLE, [row])
#         if errors:
#             print(f"BigQuery insert errors for record_id={record_id}: {errors}")
#         else:
#             print(f"Scored record_id={record_id} -> "
#                   f"risk={result['excessive_absenteeism_risk']} "
#                   f"(p={result['risk_probability']}), written to BigQuery")


# if __name__ == "__main__":
#     main()


"""
Kafka consumer — subscribes to `absence-events`, scores each record with
the same AbsenteeismModel class the FastAPI service uses (single source of
truth for scoring logic, per TRD section 10.5), and writes results to the
`absenteeism_predictions` BigQuery table (sql/02_predictions_table_ddl.sql).

Usage:
    python kafka_consumer.py
"""

import json
import os
import sys
from datetime import datetime, timezone

from kafka import KafkaConsumer
from google.cloud import bigquery

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.absenteeism_model import AbsenteeismModel
from preprocessing.feature_config import FEATURE_COLUMNS

TOPIC = "absence-events"
BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "absenteeism-scoring-consumer"

PROJECT_ID = "absenteeism-risk-platform"
DATASET = "absenteeism_analytics"
PREDICTIONS_TABLE = f"{PROJECT_ID}.{DATASET}.absenteeism_predictions"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")


def main():
    scorer = AbsenteeismModel(model_path=MODEL_PATH, scaler_path=SCALER_PATH)
    bq_client = bigquery.Client(project=PROJECT_ID)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    print(f"Listening on topic '{TOPIC}' at {BOOTSTRAP_SERVERS}, "
          f"writing scored results to {PREDICTIONS_TABLE} ...")

    for message in consumer:
        event = message.value
        record_id = event.get("record_id")

        features = {col: event[col] for col in FEATURE_COLUMNS}
        result = scorer.predict_single(features)

        row = {
            "record_id": record_id,
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "excessive_absenteeism_risk": result["excessive_absenteeism_risk"],
            "risk_probability": result["risk_probability"],
            "source": "streaming",
            **features,
        }

        # insert_rows_json() (legacy streaming insert) is disabled on
        # BigQuery Sandbox projects without billing enabled. Batch load
        # jobs work fine without billing, so we use those instead.
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        load_job = bq_client.load_table_from_json(
            [row], PREDICTIONS_TABLE, job_config=job_config
        )
        try:
            load_job.result()
            print(f"Scored record_id={record_id} -> "
                  f"risk={result['excessive_absenteeism_risk']} "
                  f"(p={result['risk_probability']}), written to BigQuery")
        except Exception as e:
            print(f"BigQuery load job failed for record_id={record_id}: {e}")


if __name__ == "__main__":
    main()