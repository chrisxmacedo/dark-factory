"""
Fixture seeder for test environment.
Loads frozen synthetic data into the test database.
All IDs are deterministic so tests can reference them by known values.

Replace the seed functions below with your project's domain data.
Keep IDs stable and hardcoded — tests reference them directly.

IMPORTANT: Only use synthetic data. No real user data, client data, or
PII should ever be committed to this repository.
"""

import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ── Seed functions — replace with your project's domain ─────────────────────
# Each function should:
#   - Use deterministic IDs (e.g. "test-user-001", "test-record-001")
#   - Use ON CONFLICT DO NOTHING for idempotency
#   - Cover enough scenarios for meaningful regression testing
#
# Minimum coverage targets:
#   - 2+ users (test user isolation / multi-tenancy)
#   - All entity types in your schema
#   - At least one relationship chain (parent -> child -> grandchild)
#   - All enum/type variants (e.g. all annotation types, all link types)
#   - At least one record with optional fields populated

def seed_users(conn):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO users (id, name, email)
               VALUES (%s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            ("test-user-001", "Test User", "test@example.com"),
        )


def main():
    print("Seeding test fixtures...")
    conn = get_connection()
    try:
        seed_users(conn)
        # Add more seed functions here
        conn.commit()
        print("Fixtures seeded successfully")
    except Exception as e:
        conn.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
