import pandas as pd
import pytest
from src import kpis, quality


def tiny():
    rows = [
        # id, country, dept, level, gender, birth, contract, fte, salary, bonus, rate, hire, exit, reason
        ("A", "France", "HR", "Professional", "M", 1990, "Permanent", 1.0, 50000, 0, 0.5, "2020-01-01", None, ""),
        ("B", "France", "HR", "Professional", "F", 1990, "Permanent", 0.5, 45000, 0, 0.5, "2020-01-01", None, ""),
        ("C", "France", "IT", "Manager", "M", 1980, "Permanent", 1.0, 70000, 1000, 0.5, "2019-01-01", "2025-06-30", "Resignation"),
        ("D", "Spain", "IT", "Manager", "F", 1985, "Permanent", 1.0, 60000, 0, 0.3, "2025-03-01", None, ""),
    ]
    cols = ["employee_id", "country", "department", "job_level", "gender", "birth_year", "contract_type", "fte",
            "base_salary_fte_eur", "annual_bonus_eur", "employer_charges_rate", "hire_date", "exit_date", "exit_reason"]
    df = pd.DataFrame(rows, columns=cols)
    df["hire_date"] = pd.to_datetime(df["hire_date"]); df["exit_date"] = pd.to_datetime(df["exit_date"])
    return df


def test_headcount_and_fte_on_date():
    s = kpis.headcount_summary(tiny(), "2025-12-31")
    assert s["headcount"] == 3          # C left in June
    assert s["fte"] == 2.5              # 1 + 0.5 + 1


def test_labour_cost_includes_fte_bonus_and_charges():
    t = kpis.labour_cost_by(tiny(), "department", "2025-12-31").set_index("department")
    # HR: (50000*1 + 45000*0.5) * 1.5 = 108750
    assert t.loc["HR", "labour_cost_eur"] == 108750


def test_attrition_uses_average_headcount():
    a = kpis.attrition(tiny(), 2025)
    assert a["leavers"] == 1
    assert a["average_headcount"] == 3.0   # (3 on 1 Jan + 3 on 31 Dec) / 2
    assert a["attrition_rate_pct"] == pytest.approx(33.3, abs=0.1)


def test_small_groups_are_hidden():
    t = pd.DataFrame({"department": ["HR", "IT"], "headcount": [3, 12], "fte": [3.0, 11.5]})
    out = kpis.suppress_small_groups(t)
    assert out.loc[0, "fte"] == "<5" and out.loc[1, "fte"] == 11.5


def test_quality_checks_catch_injected_issues():
    df = tiny()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df.loc[1, "fte"] = 1.5
    df.loc[2, "country"] = "france"
    checks = quality.run_checks(df)
    assert len(checks["duplicate_employee_id"]) == 1
    assert len(checks["fte_out_of_range"]) == 1
    assert len(checks["unknown_country_spelling"]) == 1
    cleaned, log = quality.clean(df)
    assert cleaned["employee_id"].is_unique and cleaned["country"].eq("France").sum() >= 2
