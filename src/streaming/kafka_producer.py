"""
Kafka producer — simulates new absence events arriving in real time.
Publishes randomly generated but realistically-ranged employee/event
feature records to the `absence-events` topic, at a configurable interval.
"""

import argparse
import json
import random
import time
import uuid

from kafka import KafkaProducer

TOPIC = "absence-events"
BOOTSTRAP_SERVERS = "localhost:9092"

RANGES = {
    "month_value": (1, 12),
    "day_of_week": (2, 6),
    "transportation_expense": (118, 388),
    "distance_to_work": (5, 52),
    "age": (27, 58),
    "daily_work_load_average": (205.0, 379.0),
    "body_mass_index": (19, 38),
    "children": (0, 4),
    "pets": (0, 8),
}


def random_event() -> dict:
    reason_flags = {f"reason_{i}": 0 for i in range(1, 5)}
    reason_flags[f"reason_{random.randint(1, 4)}"] = 1

    event = {
        "record_id": str(uuid.uuid4()),
        **reason_flags,
        "month_value": random.randint(*RANGES["month_value"]),
        "day_of_week": random.randint(*RANGES["day_of_week"]),
        "transportation_expense": round(random.uniform(*RANGES["transportation_expense"]), 2),
        "distance_to_work": random.randint(*RANGES["distance_to_work"]),
        "age": random.randint(*RANGES["age"]),
        "daily_work_load_average": round(random.uniform(*RANGES["daily_work_load_average"]), 3),
        "body_mass_index": random.randint(*RANGES["body_mass_index"]),
        "education_binary": random.choice([0, 1]),
        "children": random.randint(*RANGES["children"]),
        "pets": random.randint(*RANGES["pets"]),
    }
    return event


def main():
    parser = argparse.ArgumentParser(description="Simulate absence events onto Kafka.")
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds between events (default 3.0)")
    parser.add_argument("--count", type=int, default=None, help="Number of events to send (default: run forever)")
    args = parser.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Producing to topic '{TOPIC}' on {BOOTSTRAP_SERVERS} every {args.interval}s "
          f"({'forever' if args.count is None else f'{args.count} events'})...")

    sent = 0
    try:
        while args.count is None or sent < args.count:
            event = random_event()
            producer.send(TOPIC, value=event)
            producer.flush()
            sent += 1
            print(f"[{sent}] sent record_id={event['record_id']}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        producer.close()
        print(f"Total events sent: {sent}")


if __name__ == "__main__":
    main()