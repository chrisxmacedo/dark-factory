# Database best practices

Read by: all teams working on starter-api (SQLAlchemy + Alembic) and starter-web (Prisma). Cross-cutting rules for both ORMs.

## Where retention and classification requirements come from

Retention periods, PII handling, encryption-at-rest, and right-to-
erasure implementations are driven by the capability-team spec:

- `capability-team/artefacts/architecture/security-model.json` — data
  classification levels per entity
- `capability-team/artefacts/foundation/governance/*.json` — rules
  citing regulation IDs (e.g. `DP-EU-GDPR` imposes storage
  limitation; `HEALTH-US-HIPAA` imposes PHI safeguards)

Underlying libraries for context:

- `../../../../starter-regulations/data-protection.json` — full
  requirements for GDPR, HIPAA, CCPA, LGPD, PIPEDA, UAE PDPL,
  DIFC/ADGM DP, nFADP, PDPA SG, Privacy Act AU, Quebec Law 25
- `../../../../starter-standards/information-security.json` — ISO
  27018 (cloud PII processors) and NIST 800-53 Privacy baseline

## Schema design

Every table MUST have these columns:

| Column | Prisma | SQLAlchemy |
|---|---|---|
| Primary key | `id String @id @default(uuid())` | `id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)` |
| Created timestamp | `createdAt DateTime @default(now())` | `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())` |
| Updated timestamp | `updatedAt DateTime @updatedAt` | `updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())` |

Naming conventions:

| Concept | Prisma | SQLAlchemy |
|---|---|---|
| Table names | PascalCase model, plural inferred | `__tablename__ = "snake_case_plural"` |
| Column names | camelCase (`createdAt`) | snake_case (`created_at`) |
| Foreign keys | `userId String` + `@relation` | `user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))` |
| Indexes | `@@index([field])` | `index=True` on column or `Index("ix_table_col", "col")` |
| Unique constraints | `@@unique([field1, field2])` | `UniqueConstraint("col1", "col2")` |

## Migrations

### Workflow

```bash
# Prisma
npx prisma migrate dev -m "add user email index"

# SQLAlchemy + Alembic
uv run alembic revision --autogenerate -m "add user email index"
uv run alembic upgrade head
```

Always run migrations before starting the dev server. Missing migrations crash the app at startup or cause silent schema drift.

### Safe migration patterns

Use backward-compatible changes that support zero-downtime deploys:

1. **Add a nullable column** -- safe, no lock on existing rows
2. **Backfill data** -- separate migration or script, not in the same transaction as DDL
3. **Add NOT NULL constraint** -- only after backfill confirms no nulls remain
4. **Add index CONCURRENTLY** -- avoids table lock (Alembic: `op.create_index(..., postgresql_concurrently=True)`)

For column renames or type changes, use the expand-contract pattern:
1. Add new column
2. Dual-write to old and new
3. Migrate reads to new column
4. Drop old column in a later migration

### Review auto-generated migrations

Alembic autogenerate is a starting point, not a finished product. Always review:
- Does it drop columns or tables you didn't intend?
- Are index names sensible?
- Does it need explicit data migration logic?

Prisma migrations are SQL files -- read them before applying.

## Transactions

Use transactions for multi-step writes where partial completion would leave invalid state.

```typescript
// Prisma -- interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.orderItem.createMany({ data: items.map(i => ({ ...i, orderId: order.id })) });
  await tx.inventory.updateMany({ where: { id: { in: itemIds } }, data: { reserved: true } });
  return order;
});
```

```python
# SQLAlchemy -- async session transaction
async with session.begin():
    order = Order(**order_data)
    session.add(order)
    await session.flush()  # get order.id without committing
    items = [OrderItem(order_id=order.id, **i) for i in item_data]
    session.add_all(items)
    # commit happens automatically when the block exits without error
    # rollback happens automatically on exception
```

Prisma `$transaction` has a default 5-second timeout. Increase it for bulk operations:
```typescript
await prisma.$transaction(fn, { timeout: 30000 });
```

SQLAlchemy sessions auto-rollback on exception. Never catch an exception inside `session.begin()` and silently continue -- let it propagate so the rollback happens.

## Connection pooling

### Prisma

Prisma manages its own connection pool. Key settings in the connection string:

```
DATABASE_URL="postgresql://user:pass@host:5432/db?connection_limit=10&pool_timeout=30"
```

- `connection_limit` -- max connections (default 5 in Prisma, tune based on serverless vs long-running)
- `pool_timeout` -- seconds to wait for a free connection before erroring
- For serverless (Vercel): use `connection_limit=1` per instance or use Prisma Accelerate / PgBouncer

### SQLAlchemy

Configure the async engine pool:

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=10,          # steady-state connections
    max_overflow=5,        # burst above pool_size
    pool_timeout=30,       # seconds to wait for a connection
    pool_recycle=3600,     # recycle connections after 1 hour (prevents stale connections)
    pool_pre_ping=True,    # verify connection is alive before using it
)
```

### PgBouncer

When using PgBouncer (common in Supabase, cloud-hosted Postgres):
- Use `transaction` pooling mode -- each transaction gets a dedicated connection
- Disable prepared statements (`statement_cache_size=0` in SQLAlchemy, `pgbouncer=true` in Prisma connection string)
- Do not use session-level features (advisory locks, SET statements, LISTEN/NOTIFY)

## Seeding

### Principles

- Seeding must be idempotent -- safe to run multiple times without duplicating data
- Use deterministic IDs for test fixtures (`test-user-001`, not `uuid.uuid4()`)
- Separate seed data from test assertions -- seeds create the world, tests verify behaviour

### Prisma

```typescript
// prisma/seed.ts
const users = [
  { id: "test-user-001", email: "alice@test.com", name: "Alice" },
  { id: "test-user-002", email: "bob@test.com", name: "Bob" },
];

for (const user of users) {
  await prisma.user.upsert({
    where: { id: user.id },
    update: {},           // no-op if exists
    create: user,
  });
}
```

### SQLAlchemy

```python
# Use INSERT ... ON CONFLICT DO NOTHING for idempotent seeding
from sqlalchemy.dialects.postgresql import insert

stmt = insert(User).values([
    {"id": "test-user-001", "email": "alice@test.com", "name": "Alice"},
    {"id": "test-user-002", "email": "bob@test.com", "name": "Bob"},
]).on_conflict_do_nothing(index_elements=["id"])
await session.execute(stmt)
await session.commit()
```

### Canonical test identities

Every project should define a standard set of test users that all seeds and factories reference:
- `test-user-001` -- primary test user (owns most resources)
- `test-user-002` -- secondary user (for isolation and permission tests)
- `test-admin-001` -- admin user (for admin-only endpoints)

## Query patterns

### Avoid N+1 queries

The most common performance bug. Loading a list of parents then fetching children one-by-one.

```typescript
// BAD -- N+1: one query per order to get items
const orders = await prisma.order.findMany();
for (const order of orders) {
  order.items = await prisma.orderItem.findMany({ where: { orderId: order.id } });
}

// GOOD -- single query with include
const orders = await prisma.order.findMany({
  include: { items: true },
});

// GOOD -- select only needed fields
const orders = await prisma.order.findMany({
  select: { id: true, status: true, items: { select: { id: true, name: true } } },
});
```

```python
# BAD -- N+1: lazy loading triggers a query per order
orders = (await session.execute(select(Order))).scalars().all()
for order in orders:
    print(order.items)  # each access fires a SELECT

# GOOD -- eager load with joinedload
from sqlalchemy.orm import joinedload
orders = (await session.execute(
    select(Order).options(joinedload(Order.items))
)).unique().scalars().all()

# GOOD -- subqueryload for large child collections
from sqlalchemy.orm import subqueryload
orders = (await session.execute(
    select(Order).options(subqueryload(Order.items))
)).scalars().all()
```

### Pagination

Use offset pagination for admin UIs and simple lists:

```typescript
// Prisma
const orders = await prisma.order.findMany({
  skip: (page - 1) * pageSize,
  take: pageSize,
  orderBy: { createdAt: "desc" },
});
```

```python
# SQLAlchemy
stmt = (
    select(Order)
    .order_by(Order.created_at.desc())
    .offset((page - 1) * page_size)
    .limit(page_size)
)
```

Use cursor pagination for feeds, infinite scroll, or large datasets where offset becomes expensive:

```typescript
// Prisma cursor pagination
const orders = await prisma.order.findMany({
  take: pageSize,
  cursor: lastId ? { id: lastId } : undefined,
  skip: lastId ? 1 : 0,
  orderBy: { createdAt: "desc" },
});
```

### Index strategy

- Index every foreign key column (Prisma does this automatically, SQLAlchemy does not)
- Index columns used in WHERE clauses and ORDER BY
- Composite indexes: put the most selective column first
- Partial indexes for filtered queries (`WHERE status = 'active'`)
- Do not over-index -- each index slows down writes

## Data integrity

### Foreign keys

Always define foreign key constraints. They prevent orphaned records and make relationships explicit.

```prisma
model OrderItem {
  id      String @id @default(uuid())
  order   Order  @relation(fields: [orderId], references: [id], onDelete: Cascade)
  orderId String
}
```

```python
class OrderItem(Base):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
```

Choose `onDelete` deliberately:
- `CASCADE` -- child is deleted when parent is deleted (order items when order is deleted)
- `SET NULL` -- child keeps a nullable FK (comments when a user is deleted)
- `RESTRICT` -- prevent parent deletion if children exist (users with active orders)

### Unique constraints

Add unique constraints for business rules, not just the primary key:

```prisma
@@unique([userId, productId])  // one review per user per product
```

```python
__table_args__ = (UniqueConstraint("user_id", "product_id"),)
```

### Check constraints

Use check constraints for data that must always satisfy a condition:

```python
from sqlalchemy import CheckConstraint

class Product(Base):
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_product_price_positive"),
    )
```

Prisma does not support check constraints natively -- add them in a custom migration SQL file.

### Soft deletes vs hard deletes

Default to hard deletes unless there is a regulatory, audit, or recovery requirement.

Soft deletes add complexity:
- Every query needs `WHERE deleted_at IS NULL`
- Unique constraints need to be partial (exclude soft-deleted rows)
- Foreign keys still reference soft-deleted rows

If soft deletes are required:
- Add `deletedAt DateTime?` (Prisma) or `deleted_at` (SQLAlchemy)
- Add a Prisma middleware or SQLAlchemy event listener that auto-filters soft-deleted rows
- Use partial unique indexes to enforce uniqueness only on active records

For audit history without soft deletes, use the versioned model pattern (see `starter-api/CLAUDE.md`).

NEVER:
- Edit a migration file that has been applied to any environment -- create a new migration instead
- Delete migration files -- the migration history must be a complete, ordered log
- Use `db push` (Prisma) or `alembic downgrade` in production without a tested rollback plan
- Return raw database errors to the client -- catch constraint violations and return domain error codes
- Use `SELECT *` or fetch entire tables -- always select specific columns or use pagination
- Skip foreign key constraints to "keep it simple" -- orphaned data is never simple to fix
- Use auto-incrementing integer IDs -- UUIDs prevent enumeration attacks and are safe for distributed systems
- Store timestamps without timezone -- always use `timestamptz` (Postgres), `DateTime(timezone=True)` (SQLAlchemy), or `@db.Timestamptz` (Prisma)
- Perform schema changes and data backfills in the same migration -- separate DDL from DML
- Leave connections open without pooling -- always configure pool limits appropriate to the deployment environment
