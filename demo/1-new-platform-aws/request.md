> We're a ~150-person e-commerce company on AWS. We want analytics. Sources:
> three PostgreSQL service databases (~200 GB total, growing ~10%/year), one
> MongoDB database (~30 GB), and product click events (~5M/day) currently
> going to a log bucket. Finance wants daily revenue dashboards; ops
> complains reporting queries slow down the production databases; product
> wants a "real-time" funnel dashboard. The data team is two engineers. Our
> CTO is excited about building a modern lakehouse with Spark, Flink and
> Kafka. Design the data platform: components per layer, what you'd build
> first, and why. Write your design to platform-design.md.
