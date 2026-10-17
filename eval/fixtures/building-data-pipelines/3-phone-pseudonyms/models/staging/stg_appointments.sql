select appointment_id, patient_id, clinic_id, booked_at, status
from {{ source('raw', 'appointments') }}
