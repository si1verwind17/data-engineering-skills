select
  patient_id,
  full_name,
  national_id,
  phone,
  date_of_birth,
  sms_opt_in,
  _loaded_at
from {{ source('raw', 'patients') }}
qualify row_number() over (partition by patient_id order by _loaded_at desc) = 1
