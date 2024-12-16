# Commands

Commands for running med-info-bot.

## Postgres

To do RAG with Postgresql, 

### Starting Postgres

Create a DB directory:

```bash
pg_ctl init -D ./data/pg/
```

Start the Postgres server:

```bash
pg_ctl -D ./data/pg -l ./logs/postgres-server.log start
```

Start the sql command line tool:

```bash
psql -d meds
```

### Create DB assets

```sql
CREATE USER "med-info-bot" WITH PASSWORD 'SECRET';

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public 
TO "med-info-bot";

GRANT ALL PRIVILEGES
ON ALL SEQUENCES IN SCHEMA public
TO "med-info-bot";

create extension vector;

CREATE TABLE docs (
    id bigserial PRIMARY KEY,
    embedding vector(768),
    source text,
    key text,
    title text,
    text text
);

-- filling the table, then creating index is a little faster.

CREATE INDEX ON docs USING hnsw (embedding vector_l2_ops) WITH (m = 16, ef_construction = 64);
```