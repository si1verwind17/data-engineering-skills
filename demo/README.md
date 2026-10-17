# Demo

Five design documents `designing-data-platforms` wrote, one per evaluation scenario, committed as the agent wrote
them. **[Read them on the demo site](https://si1verwind17.github.io/data-engineering-skills/)**, rendered with the skill's
own `render.py`.

| Folder | The request | What it shows |
|---|---|---|
| [`1-new-platform-aws`](1-new-platform-aws/) | analytics for an e-commerce company on AWS, two data engineers, a CTO keen on a lakehouse | a new platform: read replicas first, a warehouse over a lakehouse and why, one tool per layer, what to verify before building |
| [`2-ingestion`](2-ingestion/) | ingestion for three sources after a retry duplicated orders | ingestion only: the current job recorded first, then CDC with a version guard, dead letters and redrive, deletes as tombstones |
| [`3-change-to-a-lakehouse`](3-change-to-a-lakehouse/) | new needs on a running Iceberg lakehouse | a change on the recorded platform, new parts marked: reverse ETL into the app's database, loads visible whole, protected customer data |
| [`4-sensitive-data-bigquery`](4-sensitive-data-bigquery/) | patient and card data entering BigQuery | per-column decisions, card numbers kept out, keyed pseudonyms, erasure through every layer |
| [`5-existing-platform`](5-existing-platform/) | order status within 5 minutes, with only a repo path to go on | the platform read from the repo and recorded with the file each part came from, then the change drawn on it |

Each folder holds `request.md`, the prompt as given, the design document, and `docs/data-platform/current-platform.md` when the request changes an existing platform. The runs were non-interactive: Sonnet, with
nobody to answer its questions, so each document records its questions with the assumption it proceeded on. Each was
the strongest of three runs graded in [`eval/`](../eval/designing-data-platforms/README.md).

Rebuild the site with `python3 tools/build_demo.py` (writes `_site/`: a landing page and one page per folder).
