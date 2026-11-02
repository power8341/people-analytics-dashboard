"""Generate a simulated, anonymised HR dataset for a consumer goods group.

1,470 employees over 2024-2025 across 4 countries, with hires, leavers,
salaries, bonuses and contracts. Fixed random seed so every result can be
reproduced. No real person is represented.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N = 1470
OUT = Path(__file__).resolve().parent

COUNTRIES = {"France": 0.45, "Spain": 0.20, "Poland": 0.20, "United Kingdom": 0.15}
CHARGES = {"France": 0.45, "Spain": 0.31, "Poland": 0.20, "United Kingdom": 0.14}  # employer social charges rate
SALARY_INDEX = {"France": 1.00, "Spain": 0.80, "Poland": 0.55, "United Kingdom": 1.05}
DEPARTMENTS = {"Manufacturing": 0.38, "Supply Chain": 0.16, "Sales": 0.15, "Marketing": 0.09,
               "Finance": 0.07, "R&D": 0.07, "IT": 0.05, "HR": 0.03}
LEVELS = {"Operator": (0.40, 30000), "Technician": (0.25, 38000), "Professional": (0.20, 50000),
          "Manager": (0.11, 68000), "Senior Manager": (0.04, 95000)}
MANUFACTURING_LEVELS = {"Operator": 0.65, "Technician": 0.22, "Professional": 0.08, "Manager": 0.04, "Senior Manager": 0.01}


def pick(rng, mapping, size):
    keys = list(mapping)
    probs = np.array([v[0] if isinstance(v, tuple) else v for v in mapping.values()], dtype=float)
    return rng.choice(keys, size=size, p=probs / probs.sum())


def generate(n=N, seed=SEED):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"employee_id": [f"E{100000 + i}" for i in range(n)]})
    df["country"] = pick(rng, COUNTRIES, n)
    df["department"] = pick(rng, DEPARTMENTS, n)
    df["job_level"] = pick(rng, LEVELS, n)
    is_manu = df["department"].eq("Manufacturing")
    df.loc[is_manu, "job_level"] = pick(rng, MANUFACTURING_LEVELS, is_manu.sum())
    # gender mix differs by department, as in many manufacturing groups
    female_share = df["department"].map({"Manufacturing": 0.30, "Supply Chain": 0.35, "Sales": 0.50, "Marketing": 0.65,
                                         "Finance": 0.58, "R&D": 0.42, "IT": 0.28, "HR": 0.75})
    df["gender"] = np.where(rng.random(n) < female_share, "F", "M")
    # fewer women at the most senior levels (the pattern the pay gap analysis should reveal)
    senior = df["job_level"].isin(["Manager", "Senior Manager"]) & df["gender"].eq("F") & (rng.random(n) < 0.45)
    df.loc[senior, "gender"] = "M"
    df["birth_year"] = rng.integers(1962, 2005, n)
    df["contract_type"] = rng.choice(["Permanent", "Fixed-term", "Apprentice"], n, p=[0.86, 0.10, 0.04])
    df["fte"] = np.where(rng.random(n) < 0.12, rng.choice([0.5, 0.6, 0.8], n), 1.0)
    df.loc[df["contract_type"].eq("Apprentice"), ["job_level", "fte"]] = ["Technician", 1.0]

    base = df["job_level"].map({k: v[1] for k, v in LEVELS.items()}) * df["country"].map(SALARY_INDEX)
    noise = rng.normal(1.0, 0.08, n)
    gender_effect = np.where(df["gender"].eq("F"), 0.96, 1.0)  # small adjusted gap at same level and country
    df["base_salary_fte_eur"] = (base * noise * gender_effect).round(-1)
    df.loc[df["contract_type"].eq("Apprentice"), "base_salary_fte_eur"] = (
        df.loc[df["contract_type"].eq("Apprentice"), "country"].map({"France": 15000, "Spain": 12000, "Poland": 9000, "United Kingdom": 16000}))
    bonus_rate = df["job_level"].map({"Operator": 0.03, "Technician": 0.04, "Professional": 0.08, "Manager": 0.12, "Senior Manager": 0.20})
    df["annual_bonus_eur"] = (df["base_salary_fte_eur"] * df["fte"] * bonus_rate * rng.uniform(0.6, 1.3, n)).round(-1)
    df["employer_charges_rate"] = df["country"].map(CHARGES)

    # hire and exit dates
    hire_days = rng.integers(0, 365 * 20, n)
    df["hire_date"] = (pd.Timestamp("2025-12-31") - pd.to_timedelta(hire_days, unit="D")).normalize()
    leave = rng.random(n) < 0.17
    exit_days = rng.integers(0, 730, n)
    exit_date = pd.Timestamp("2024-01-01") + pd.to_timedelta(exit_days, unit="D")
    df["exit_date"] = pd.NaT
    df.loc[leave, "exit_date"] = exit_date[leave]
    df.loc[df["exit_date"] <= df["hire_date"], "exit_date"] = pd.NaT
    df["exit_reason"] = np.where(df["exit_date"].notna(), rng.choice(["Resignation", "End of contract", "Retirement", "Dismissal"], n, p=[0.55, 0.25, 0.12, 0.08]), "")
    return df


def add_quality_issues(df, seed=SEED):
    """Inject a few realistic data issues so the quality checks have something to catch."""
    rng = np.random.default_rng(seed + 1)
    dirty = df.copy()
    dup = dirty.sample(3, random_state=1)
    dirty = pd.concat([dirty, dup], ignore_index=True)                      # 3 duplicated employees
    idx = rng.choice(dirty.index, 5, replace=False)
    dirty.loc[idx[:2], "department"] = None                                 # 2 missing departments
    dirty.loc[idx[2], "base_salary_fte_eur"] = -100                         # 1 negative salary
    dirty.loc[idx[3], "fte"] = 1.5                                          # 1 impossible FTE
    dirty.loc[idx[4], "country"] = "france"                                 # 1 inconsistent spelling
    return dirty


if __name__ == "__main__":
    clean = generate()
    add_quality_issues(clean).to_csv(OUT / "hr_employees_raw.csv", index=False)
    print(f"Wrote {OUT / 'hr_employees_raw.csv'}: {len(clean) + 3} rows (with injected issues)")
