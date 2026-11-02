# Data dictionary (`data/hr_employees_clean.csv`)

| Column | Meaning |
|---|---|
| employee_id | Anonymous ID (no names or personal identifiers) |
| country, department, job_level | Organisation |
| gender | F or M |
| birth_year, age_band | Age band is computed for reporting; birth year never appears in reports |
| contract_type | Permanent, Fixed-term, Apprentice |
| fte | Working time ratio (0.5 to 1.0) |
| base_salary_fte_eur | Yearly base salary for a full-time position |
| annual_bonus_eur | Yearly bonus |
| employer_charges_rate | Employer social charges rate for the country |
| annual_pay_eur | base_salary_fte_eur x fte + annual_bonus_eur |
| labour_cost_eur | annual_pay_eur x (1 + employer_charges_rate) |
| hire_date, exit_date, exit_reason | Employment dates; empty exit date = still employed |
