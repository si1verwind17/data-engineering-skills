select
  p.patient_id,
  p.national_id,
  p.phone,
  date_diff(current_date(), p.date_of_birth, year) as age,
  count(a.appointment_id) as visits
from {{ ref('stg_patients') }} p
left join {{ ref('stg_appointments') }} a using (patient_id)
group by 1, 2, 3, 4
