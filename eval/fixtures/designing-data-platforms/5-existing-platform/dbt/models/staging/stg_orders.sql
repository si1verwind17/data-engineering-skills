-- one row per order: the latest version from the nightly extracts
select *
from (
    select *, row_number() over (partition by order_id order by updated_at desc) as rn
    from {{ source('raw', 'orders') }}
)
where rn = 1
