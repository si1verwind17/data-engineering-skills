-- rebuilt after every load
drop table if exists core.orders;
create table core.orders as
select order_id, customer_id, status, amount_cents, updated_at
from raw.orders;
