select patient_id, full_name, phone
from {{ ref('stg_patients') }}
where sms_opt_in
