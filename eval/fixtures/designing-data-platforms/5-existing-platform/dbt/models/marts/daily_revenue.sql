select date(created_at) as order_date, status, count(*) as orders, sum(total_amount) as revenue
from {{ ref('stg_orders') }}
group by 1, 2
