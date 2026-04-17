# Migration safety

Read by: all teams working on starter-api (Alembic) and starter-web (Prisma). Cross-cutting rules for safe, zero-downtime schema changes.

## Always migrate before serving

Run migrations as the first step before any service starts. A missing migration crashes the API at startup or causes silent schema drift.

**Locally:**

```bash
# Alembic
uv run alembic upgrade head
uv run uvicorn src.main:app --reload

# Prisma
npx prisma migrate deploy
npm run dev
```

**Docker (init container pattern):**

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  migrate:
    build: .
    command: ["alembic", "upgrade", "head"]  # or: npx prisma migrate deploy
    restart: "no"
    depends_on:
      db:
        condition: service_healthy

  api:
    build: .
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
    depends_on:
      migrate:
        condition: service_completed_successfully
      db:
        condition: service_healthy
```

The `migrate` container runs exactly once before any app container starts. `restart: "no"` ensures it does not retry on failure -- a failed migration should block the deploy, not silently loop.

## Backward-compatible changes only

Every migration must be safe to run while the old version of the code is still serving traffic. During a rolling deploy, old and new code run simultaneously.

**Safe changes:**

- Add a column as nullable (no default needed, old code ignores it)
- Add a column with a server default (old code ignores it, new rows get the default)
- Add a new table (old code does not reference it)
- Add an index (old code is unaffected)

**Unsafe changes -- never do these in a single migration:**

- Rename a column (old code queries the old name and breaks)
- Drop a column that old code reads (old code gets a missing column error)
- Change a column type incompatibly (old code sends the wrong type)
- Add a NOT NULL constraint on a column that old code does not populate

## Expand-contract pattern

For breaking schema changes, split the work into two migrations separated by a code deploy.

### Step 1: EXPAND

Add the new column or table alongside the old one. Deploy code that writes to both.

```python
# Alembic -- expand migration
def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(255), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "display_name")
```

```sql
-- Prisma -- expand migration (generated SQL)
ALTER TABLE "User" ADD COLUMN "displayName" TEXT;
```

Deploy application code that:
1. Writes to both `name` and `display_name` on every update
2. Reads from `display_name`, falling back to `name` if null

### Step 2: CONTRACT

After all old code is gone and the backfill is complete, drop the old column.

```python
# Alembic -- contract migration (deployed later)
def upgrade() -> None:
    op.drop_column("users", "name")

def downgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(255), nullable=True))
```

Never combine expand and contract in the same migration. The contract migration ships only after the expand has been deployed to all environments and the backfill is verified.

## Data backfills

Large table backfills must be batched to avoid locking the table and overwhelming the database.

```python
# Alembic -- batched backfill
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    conn = op.get_bind()
    batch_size = 1000
    last_id = None

    while True:
        query = sa.text("""
            UPDATE users
            SET display_name = name
            WHERE display_name IS NULL
              AND (:last_id IS NULL OR id > :last_id)
            ORDER BY id
            LIMIT :batch_size
            RETURNING id
        """)
        result = conn.execute(query, {"last_id": last_id, "batch_size": batch_size})
        rows = result.fetchall()

        if not rows:
            break

        last_id = rows[-1][0]
        print(f"Backfilled {len(rows)} rows, last_id={last_id}")
```

```typescript
// Prisma -- batched backfill script
let lastId: string | undefined;
const batchSize = 1000;

while (true) {
  const users = await prisma.user.findMany({
    where: {
      displayName: null,
      ...(lastId ? { id: { gt: lastId } } : {}),
    },
    orderBy: { id: "asc" },
    take: batchSize,
  });

  if (users.length === 0) break;

  await prisma.$transaction(
    users.map((u) =>
      prisma.user.update({
        where: { id: u.id },
        data: { displayName: u.name },
      })
    )
  );

  lastId = users[users.length - 1].id;
  console.log(`Backfilled ${users.length} rows, lastId=${lastId}`);
}
```

Rules for backfills:
- Batch size of 1000 rows, paginated with `WHERE id > last_processed`
- Never run an unbounded `UPDATE` on a large table
- Backfills must be idempotent -- safe to re-run without duplicating or corrupting data
- Log progress so you can monitor and resume
- Separate DDL (schema changes) from DML (data backfills) -- never mix them in the same migration

## Index creation

Creating an index on a large table locks the table for the duration of the build. Use concurrent index creation to avoid blocking reads and writes.

**Alembic:**

```python
def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_users_email",
            "users",
            ["email"],
            unique=True,
            postgresql_concurrently=True,
        )

def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
```

When using `postgresql_concurrently=True`, the migration cannot run inside a transaction. The `autocommit_block()` context manager handles this.

**Prisma:**

Prisma generates standard `CREATE INDEX` statements. For large tables, replace the generated migration SQL with a concurrent version:

```sql
-- prisma/migrations/20240101000000_add_email_index/migration.sql
-- Replace the generated CREATE INDEX with:
CREATE INDEX CONCURRENTLY "User_email_idx" ON "User"("email");
```

Keep the `@@index([email])` in `schema.prisma` so Prisma knows the index exists.

## Migration ordering

Migrations are applied in sequence. The ordering is the source of truth for the database state.

- Never edit a migration after it has been applied to any environment (dev, staging, production)
- Never delete migration files -- the migration history must be a complete, ordered log
- If a migration is wrong, create a new migration that undoes it -- never go back and modify the original
- Each migration should be a self-contained, atomic change

## Testing migrations

Run the full migration chain from an empty database in CI, not just the latest migration. This catches ordering issues, missing dependencies, and broken rollbacks.

```bash
# Alembic -- test full chain
uv run alembic upgrade head        # forward: empty -> current
uv run alembic downgrade base      # rollback: current -> empty
uv run alembic upgrade head        # forward again to verify round-trip

# Prisma -- test full chain
npx prisma migrate deploy          # apply all migrations
npx prisma db seed                 # verify seeding works after migration
```

CI should verify:
1. Forward migration from empty database succeeds
2. Rollback works (Alembic -- `downgrade base`; Prisma -- not built-in, see rollback strategy below)
3. Forward migration again after rollback succeeds
4. Seeding works after the full migration chain

## Docker migration patterns

The init container pattern ensures migrations run exactly once before any application code starts.

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  migrate:
    build: .
    command: ["alembic", "upgrade", "head"]
    restart: "no"
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: ${DATABASE_URL}

  api:
    build: .
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
    depends_on:
      migrate:
        condition: service_completed_successfully
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: ${DATABASE_URL}

  web:
    build: ./web
    command: ["npm", "run", "start"]
    depends_on:
      migrate:
        condition: service_completed_successfully
```

Key details:
- `restart: "no"` on the migrate container -- it runs once and exits
- `condition: service_healthy` on the database -- migrate waits for Postgres to accept connections
- `condition: service_completed_successfully` on the migrate container -- app containers wait for migrations to finish
- If the migrate container fails, all dependent services refuse to start -- this is the correct behavior

## Rollback strategy

### Alembic

Alembic has built-in rollback support via `downgrade`:

```bash
# Roll back one migration
uv run alembic downgrade -1

# Roll back to a specific revision
uv run alembic downgrade abc123

# Roll back to empty database (development only)
uv run alembic downgrade base
```

Always test rollback in development before relying on it in production. Every `upgrade()` function should have a corresponding `downgrade()` that cleanly reverses the change.

### Prisma

Prisma has no built-in rollback command. To undo a migration:

1. Create a new migration that reverses the change:
   ```bash
   npx prisma migrate dev -m "revert add display name"
   ```
2. Write the reverse SQL manually in the generated migration file
3. Apply it forward -- Prisma only moves forward

For emergencies in production, you can apply raw SQL against the database, but this creates drift between the migration history and the actual schema. Always follow up with a Prisma migration that matches the actual state.

## Environment-specific migration commands

Different environments require different migration commands. Using the wrong command in the wrong environment is a common source of incidents.

| Environment | Alembic | Prisma |
|---|---|---|
| Development | `alembic revision --autogenerate` + `alembic upgrade head` | `npx prisma migrate dev` (generates + applies) |
| CI | `alembic upgrade head` (apply only) | `npx prisma migrate deploy` (apply only) |
| Staging | `alembic upgrade head` (apply only) | `npx prisma migrate deploy` (apply only) |
| Production | `alembic upgrade head` (apply only) | `npx prisma migrate deploy` (apply only) |

- `migrate dev` (Prisma) and `--autogenerate` (Alembic) generate new migration files. These commands must only run in development.
- `migrate deploy` (Prisma) and `upgrade head` (Alembic) apply existing migrations without generating anything. These are the only commands that should run in CI, staging, and production.
- Never auto-generate migrations in non-dev environments -- migration files are committed to the repo and applied from there.

NEVER:
- Edit a migration file that has been applied to any environment -- create a new migration instead
- Delete migration files -- the migration history must be a complete, ordered log
- Run `prisma migrate dev` or `alembic revision --autogenerate` in CI, staging, or production
- Run an unbounded UPDATE or DELETE in a migration -- always batch
- Create an index without CONCURRENTLY on a large table in production
- Mix DDL (schema changes) and DML (data backfills) in the same migration
- Skip migration testing in CI -- run the full chain from empty database
- Deploy a contract migration before the expand migration is live in all environments
- Assume rollback works -- test it in development first
