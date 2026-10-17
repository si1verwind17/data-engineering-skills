> Design ingestion into our warehouse (Postgres-based today, may move to a
> lakehouse later) for three sources, in ingestion-design.md:
>
> - `orders` in a PostgreSQL service DB (40M rows, ~200k changes/day). Rows
>   have `updated_at`. Cancelled orders are hard-deleted within 24h. The
>   service sometimes runs transactions lasting several minutes.
> - A document database the team says has no CDC support in our tooling.
> - A third-party SaaS REST API (rate-limited, paginated, data editable for
>   30 days after creation).
>
> Today an hourly Python job selects `updated_at > last_run_time` and
> appends to the warehouse. Last week a run failed halfway, was retried, and
> finance found duplicate orders. Ops also wants order status on a
> dashboard within a minute of changing. Propose the design.
