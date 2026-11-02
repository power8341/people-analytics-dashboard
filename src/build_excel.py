"""Build the Excel version of the KPIs with live formulas (COUNTIFS, SUMIFS,
AVERAGEIFS, XLOOKUP), so every Power BI figure can be cross-checked in Excel."""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HEAD = PatternFill("solid", fgColor="1F3A5F")
WHITE = Font(bold=True, color="FFFFFF")


def _header(ws, row, values):
    for i, v in enumerate(values, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.fill, c.font = HEAD, WHITE


def build(df: pd.DataFrame, out: Path, date: str = "2025-12-31") -> None:
    d = pd.Timestamp(date)
    data = df.copy()
    data["active_flag"] = ((data["hire_date"] <= d) & (data["exit_date"].isna() | (data["exit_date"] > d))).astype(int)
    data["leaver_2025"] = ((data["exit_date"] >= "2025-01-01") & (data["exit_date"] <= "2025-12-31")).astype(int)
    cols = ["employee_id", "country", "department", "job_level", "gender", "age_band", "contract_type", "fte",
            "base_salary_fte_eur", "annual_bonus_eur", "labour_cost_eur", "active_flag", "leaver_2025"]
    data = data[cols]
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    _header(ws, 1, cols)
    for r in data.itertuples(index=False):
        ws.append(list(r))
    n = len(data) + 1
    col = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
    rng = lambda c: f"Data!${col[c]}$2:${col[c]}${n}"
    for i in range(1, len(cols) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 16

    k = wb.create_sheet("KPIs")
    k["A1"], k["A1"].font = f"People KPIs on {date} (formulas, active employees only)", Font(bold=True, size=13)
    k["A3"], k["B3"] = "Headcount", f"=SUM({rng('active_flag')})"
    k["A4"], k["B4"] = "FTE", f"=SUMIFS({rng('fte')},{rng('active_flag')},1)"
    k["A5"], k["B5"] = "Annual labour cost (EUR)", f"=SUMIFS({rng('labour_cost_eur')},{rng('active_flag')},1)"
    k["A6"], k["B6"] = "Labour cost per FTE (EUR)", "=B5/B4"
    k["A7"], k["B7"] = "Leavers in 2025", f"=SUM({rng('leaver_2025')})"
    k["A8"], k["B8"] = "Women share (%)", f"=COUNTIFS({rng('active_flag')},1,{rng('gender')},\"F\")/B3*100"
    k["A9"], k["B9"] = "Avg base salary men (EUR, excl. apprentices)", f"=AVERAGEIFS({rng('base_salary_fte_eur')},{rng('active_flag')},1,{rng('gender')},\"M\",{rng('contract_type')},\"<>Apprentice\")"
    k["A10"], k["B10"] = "Avg base salary women (EUR, excl. apprentices)", f"=AVERAGEIFS({rng('base_salary_fte_eur')},{rng('active_flag')},1,{rng('gender')},\"F\",{rng('contract_type')},\"<>Apprentice\")"
    k["A11"], k["B11"] = "Unadjusted gender pay gap (%)", "=(B9-B10)/B9*100"
    _header(k, 13, ["Department", "Headcount", "FTE", "Labour cost (EUR)", "Cost per FTE (EUR)"])
    for i, dep in enumerate(sorted(data["department"].unique()), start=14):
        k.cell(i, 1, dep)
        k.cell(i, 2, f"=COUNTIFS({rng('department')},A{i},{rng('active_flag')},1)")
        k.cell(i, 3, f"=SUMIFS({rng('fte')},{rng('department')},A{i},{rng('active_flag')},1)")
        k.cell(i, 4, f"=SUMIFS({rng('labour_cost_eur')},{rng('department')},A{i},{rng('active_flag')},1)")
        k.cell(i, 5, f"=IF(C{i}=0,0,D{i}/C{i})")
    for row in k.iter_rows(min_row=3, max_row=40, min_col=2, max_col=5):
        for c in row:
            c.number_format = "#,##0.0"
    k.column_dimensions["A"].width = 46
    for c in "BCDE":
        k.column_dimensions[c].width = 18

    lk = wb.create_sheet("Lookup")
    lk["A1"], lk["A1"].font = "Employee lookup (XLOOKUP, Excel 365)", Font(bold=True, size=13)
    lk["A3"], lk["B3"] = "Employee ID", data["employee_id"].iloc[0]
    lk["B2"], lk["C2"] = "XLOOKUP", "INDEX / MATCH (older Excel)"
    for i, f in enumerate(["department", "job_level", "country", "fte", "labour_cost_eur"], start=4):
        lk.cell(i, 1, f)
        lk.cell(i, 2, f"=XLOOKUP($B$3,{rng('employee_id')},{rng(f)},\"not found\")")
        lk.cell(i, 3, f"=INDEX({rng(f)},MATCH($B$3,{rng('employee_id')},0))")
    lk["A11"] = "Change the ID in B3 to look up another employee. Real HR files should restrict this sheet to authorised users."
    lk["A11"].alignment = Alignment(wrap_text=True)
    lk.column_dimensions["A"].width = 30
    lk.column_dimensions["B"].width = 22
    lk.column_dimensions["C"].width = 26

    wb.move_sheet("KPIs", offset=-1)
    wb.active = 0
    wb.save(out)
