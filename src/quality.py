"""Data quality checks and cleaning for the HR dataset.

Every check returns the rows it flags, so the quality report can say exactly
what was wrong and how it was fixed. HR figures are only shared once these
checks pass.
"""
import pandas as pd

VALID_COUNTRIES = {"France", "Spain", "Poland", "United Kingdom"}
REQUIRED = ["employee_id", "country", "department", "job_level", "gender", "hire_date", "base_salary_fte_eur", "fte"]


def run_checks(df: pd.DataFrame) -> dict:
    checks = {
        "duplicate_employee_id": df[df.duplicated("employee_id", keep="first")],
        "missing_required_field": df[df[REQUIRED].isna().any(axis=1)],
        "negative_or_zero_salary": df[df["base_salary_fte_eur"] <= 0],
        "fte_out_of_range": df[(df["fte"] <= 0) | (df["fte"] > 1)],
        "unknown_country_spelling": df[~df["country"].isin(VALID_COUNTRIES) & df["country"].notna()],
        "exit_before_hire": df[pd.to_datetime(df["exit_date"]) < pd.to_datetime(df["hire_date"])],
    }
    return checks


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    log = []
    out = df.copy()
    out["hire_date"] = pd.to_datetime(out["hire_date"])
    out["exit_date"] = pd.to_datetime(out["exit_date"])
    n = len(out)
    out = out.drop_duplicates("employee_id", keep="first")
    log.append(f"Removed {n - len(out)} duplicated employee rows")
    fixed = out["country"].str.title().replace({"United kingdom": "United Kingdom"})
    log.append(f"Standardised {int((fixed != out['country']).sum())} country spellings")
    out["country"] = fixed
    bad = out["department"].isna() | (out["base_salary_fte_eur"] <= 0) | (out["fte"] <= 0) | (out["fte"] > 1)
    log.append(f"Set aside {int(bad.sum())} rows for HR to correct at the source (missing department, invalid salary or FTE)")
    out = out[~bad]
    return out.reset_index(drop=True), log


def quality_report(raw: pd.DataFrame) -> str:
    lines = ["# Data quality report", "", f"Rows received: {len(raw)}", "", "| Check | Rows flagged |", "|---|---|"]
    for name, rows in run_checks(raw).items():
        lines.append(f"| {name.replace('_', ' ')} | {len(rows)} |")
    cleaned, log = clean(raw)
    lines += ["", "## Actions", ""] + [f"- {x}" for x in log] + ["", f"Rows used for reporting: {len(cleaned)}"]
    return "\n".join(lines)
