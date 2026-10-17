> We have a lakehouse on AWS: Iceberg tables on S3, Glue catalog, Spark +
> dbt for transforms, Trino for queries, Superset for BI. Raw order events
> land partitioned by ingestion hour; there are now millions of small files
> and queries are slow. New needs, design them in model-design.md:
>
> - Finance: monthly revenue by region and product category.
> - Customer service: a searchable, filterable list of individual orders
>   (by customer, status, date) with CSV export, used by ~200 agents all day.
> - Merchant portal (our app, backed by its own PostgreSQL): each merchant
>   sees their daily sales aggregates. Today the app computes these live
>   from its Postgres and it is eating CPU/memory.
> - Product: how each customer's loyalty tier changed over time.
> - Late events: mobile clients sometimes send events up to 3 days late.
