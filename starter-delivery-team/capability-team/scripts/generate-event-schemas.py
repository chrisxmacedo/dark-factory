#!/usr/bin/env python3
"""
Generate Avro schema files (.avsc) from event catalogue payload definitions.

Reads all event catalogues (journey-level and central), extracts payload
schemas, and produces one .avsc file per event organised by topic.

Output: artefacts/schemas/events/{topic}/{event-name}.avsc

Usage: python3 generate-event-schemas.py
"""

import json
import re
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model" / "event-catalogue.json"
OUTPUT = ARTEFACTS / "schemas" / "events"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


# Map JSON/informal types to Avro types
TYPE_MAP = {
    "string": "string",
    "str": "string",
    "uuid": "string",
    "UUID": "string",
    "integer": "int",
    "int": "int",
    "number": "double",
    "float": "double",
    "double": "double",
    "decimal": {"type": "bytes", "logicalType": "decimal", "precision": 18, "scale": 4},
    "boolean": "boolean",
    "bool": "boolean",
    "date": {"type": "int", "logicalType": "date"},
    "datetime": {"type": "long", "logicalType": "timestamp-millis"},
    "timestamp": {"type": "long", "logicalType": "timestamp-millis"},
    "ISO 8601": {"type": "long", "logicalType": "timestamp-millis"},
    "array": {"type": "array", "items": "string"},
    "object": "string",  # serialised as JSON string in Avro
    "enum": "string",  # enums become strings with doc noting valid values
}


def to_avro_type(field_type, field_name="", nullable=True):
    """Convert an informal type string to an Avro type."""
    if not field_type:
        return ["null", "string"] if nullable else "string"

    if isinstance(field_type, dict):
        # Nested object type — serialise as JSON string
        return ["null", "string"] if nullable else "string"

    if isinstance(field_type, list):
        return ["null", "string"] if nullable else "string"

    ft = str(field_type).lower().strip()

    # Handle "string (UUID)" or "string (ISO 8601)" patterns
    base = ft.split("(")[0].strip().split(" ")[0]

    if "iso 8601" in ft or "datetime" in ft or "timestamp" in ft:
        avro = {"type": "long", "logicalType": "timestamp-millis"}
    elif "date" in ft and "time" not in ft:
        avro = {"type": "int", "logicalType": "date"}
    elif "decimal" in ft or "currency" in ft or "amount" in ft:
        avro = {"type": "bytes", "logicalType": "decimal", "precision": 18, "scale": 4}
    elif base in TYPE_MAP:
        avro = TYPE_MAP[base]
    else:
        avro = "string"

    if nullable:
        return ["null", avro]
    return avro


def pascal_to_snake(name):
    """Convert PascalCase or camelCase to snake_case."""
    s = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', name)
    s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', s)
    return s.lower()


def event_name_to_filename(name):
    """Convert EventName to kebab-case filename."""
    kebab = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', name)
    kebab = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '-', kebab)
    return kebab.lower()


def extract_events_from_catalogue(data):
    """Extract all events from a catalogue, handling various structures."""
    events = []

    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and ("name" in item or "event_id" in item):
                        events.append(item)
            elif isinstance(val, dict) and ("name" in val or "event_id" in val):
                events.append(val)

    return events


def build_avro_schema(event):
    """Build an Avro schema from an event definition."""
    name = event.get("name", "Unknown")
    event_id = event.get("event_id", "")
    topic = event.get("topic", "unknown")
    source = event.get("source_service", "")
    ce_type = event.get("cloudevents_type", "")
    payload = event.get("payload_schema", {})

    # Build Avro fields from payload schema
    avro_fields = []

    if isinstance(payload, dict):
        for field_name, field_def in payload.items():
            if isinstance(field_def, dict):
                field_type = field_def.get("type", "string")
                description = field_def.get("description", "")
                derived = field_def.get("derived_from", "")
                doc_parts = []
                if description:
                    doc_parts.append(description)
                if derived:
                    doc_parts.append(f"Derived from: {derived}")

                avro_field = {
                    "name": pascal_to_snake(field_name) if not "_" in field_name else field_name,
                    "type": to_avro_type(field_type),
                }
                if doc_parts:
                    avro_field["doc"] = ". ".join(doc_parts)

                avro_fields.append(avro_field)
            elif isinstance(field_def, str):
                avro_fields.append({
                    "name": pascal_to_snake(field_name) if "_" not in field_name else field_name,
                    "type": to_avro_type(field_def),
                })

    # Add CloudEvents envelope fields
    envelope_fields = [
        {"name": "ce_specversion", "type": "string", "default": "1.0", "doc": "CloudEvents spec version"},
        {"name": "ce_type", "type": "string", "default": ce_type or f"uk.bank.{topic}.{pascal_to_snake(name)}", "doc": "CloudEvents type"},
        {"name": "ce_source", "type": "string", "doc": f"Source service: {source}"},
        {"name": "ce_id", "type": "string", "doc": "Unique event ID (UUID)"},
        {"name": "ce_time", "type": {"type": "long", "logicalType": "timestamp-millis"}, "doc": "Event timestamp"},
    ]

    schema = {
        "type": "record",
        "name": name,
        "namespace": f"uk.bank.events.{topic.replace('.', '.').replace('/', '.')}",
        "doc": f"Event: {name} ({event_id}). Source: {source}. Topic: {topic}.",
        "fields": envelope_fields + avro_fields,
    }

    return schema


def main():
    print(f"\n{'='*60}")
    print("Generating Avro schemas from event catalogues")
    print(f"{'='*60}\n")

    # Collect all events from all sources
    all_events = {}

    # From journey-level catalogues
    for evt_file in sorted(MODELS.rglob("events/event-catalogue.json")):
        try:
            data = json.load(open(evt_file))
            events = extract_events_from_catalogue(data)
            for evt in events:
                name = evt.get("name", "")
                if name and name not in all_events:
                    all_events[name] = evt
        except (json.JSONDecodeError, KeyError):
            pass

    # From central catalogue
    if CENTRAL.exists():
        try:
            data = json.load(open(CENTRAL))
            events = extract_events_from_catalogue(data)
            for evt in events:
                name = evt.get("name", "")
                if name and name not in all_events:
                    all_events[name] = evt
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"Found {len(all_events)} unique events\n")

    # Generate schemas
    generated = 0
    skipped = 0
    by_topic = {}

    for name, evt in sorted(all_events.items()):
        topic = evt.get("topic", "unknown")
        if not topic:
            topic = "unknown"

        # Normalise topic to directory-safe name
        topic_dir = topic.replace(".", "/").replace(" ", "-").lower()

        # Skip events with no payload schema
        payload = evt.get("payload_schema", {})
        if not payload or (isinstance(payload, dict) and len(payload) == 0):
            skipped += 1
            continue

        # Build and write schema
        schema = build_avro_schema(evt)
        filename = event_name_to_filename(name)

        out_dir = OUTPUT / topic_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / f"{filename}.avsc"
        with open(out_path, "w") as f:
            json.dump(schema, f, indent=2)

        generated += 1
        by_topic[topic] = by_topic.get(topic, 0) + 1

    print(f"Generated: {generated} schemas")
    print(f"Skipped:   {skipped} events (no payload schema)")
    print(f"\nBy topic:")
    for topic, count in sorted(by_topic.items()):
        print(f"  {topic}: {count} schemas")

    print(f"\nOutput: {OUTPUT}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
