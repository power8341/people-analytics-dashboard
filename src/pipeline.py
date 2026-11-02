"""Run the whole pipeline: quality checks, cleaning, KPIs, Excel workbook,
CSV extracts for Power BI and README charts."""
import json
from pathlib import Path
import pandas as pd
from src import quality, kpis, build_excel, charts

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "hr_employees_raw.csv"
REP = ROOT / "reports"
DATE = "2025-12-31"


def main():
    raw = pd.read_csv(RAW)
    REP.mkdir(exist_ok=True)
    (REP / "data_quality_report.md").write_text(quality.quality_report(raw), encoding="utf-8")
    clean, _ = quality.clean(raw)
    full = kpis.add_derived(clean)
    full.to_csv(ROOT / "data" / "hr_employees_clean.csv", index=False)  # Power BI source

    summary = {"as_of": DATE, **kpis.headcount_summary(clean, DATE),
               "attrition_2024": kpis.attrition(clean, 2024), "attrition_2025": kpis.attrition(clean, 2025),
               "gender_pay_gap": kpis.gender_pay_gap(clean, DATE)}
    lc = kpis.labour_cost_by(clean, "department", DATE)
    summary["labour_cost_total_eur"] = float(lc["labour_cost_eur"].sum())
    summary["labour_cost_per_fte_eur"] = round(summary["labour_cost_total_eur"] / summary["fte"], 0)
    (REP / "kpi_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    hc_dep = kpis.headcount_by(clean, "department", DATE)
    hc_ctry = kpis.headcount_by(clean, "country", DATE)
    hc_age = kpis.headcount_by(full, "age_band", DATE)
    women = kpis.women_share_by_level(clean, DATE)
    hc_dep.to_csv(REP / "headcount_by_department.csv", index=False)
    hc_ctry.to_csv(REP / "headcount_by_country.csv", index=False)
    hc_age.to_csv(REP / "headcount_by_age_band.csv", index=False)
    lc.to_csv(REP / "labour_cost_by_department.csv", index=False)
    women.to_csv(REP / "women_share_by_level.csv", index=False)

    charts.bar(hc_dep, "department", "headcount", "Headcount by department (31 Dec 2025)", REP / "headcount_by_department.png")
    charts.bar(lc, "department", "cost_per_fte_eur", "Labour cost per FTE by department (EUR)", REP / "labour_cost_per_fte.png", color="#3C7A89")
    charts.women_by_level(women, REP / "women_share_by_level.png")
    build_excel.build(full, ROOT / "excel" / "people_kpis.xlsx", DATE)
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
