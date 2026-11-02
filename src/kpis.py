"""People Analytics and HR controlling KPIs.

Definitions follow common HR controlling practice:
- headcount: people employed on a date (exit date after it or empty)
- FTE: sum of working-time ratios (two half-time employees = 1 FTE)
- annual labour cost: base salary x FTE + bonus, plus employer social charges
- attrition rate: leavers in the year / average headcount (start and end of year)
- unadjusted gender pay gap: (average men pay - average women pay) / average men pay
- adjusted gap: the same, compared within each job level and country, weighted by headcount
Groups of fewer than 5 people are hidden to protect confidentiality.
"""
import pandas as pd

MIN_GROUP = 5
AGE_BANDS = [(0, 25, "<25"), (25, 35, "25-34"), (35, 45, "35-44"), (45, 55, "45-54"), (55, 100, "55+")]


def active_on(df: pd.DataFrame, date: str) -> pd.DataFrame:
    d = pd.Timestamp(date)
    return df[(df["hire_date"] <= d) & (df["exit_date"].isna() | (df["exit_date"] > d))]


def add_derived(df: pd.DataFrame, ref_year: int = 2025) -> pd.DataFrame:
    out = df.copy()
    age = ref_year - out["birth_year"]
    out["age_band"] = pd.cut(age, [b[0] for b in AGE_BANDS] + [100], right=False, labels=[b[2] for b in AGE_BANDS]).astype(str)
    out["annual_pay_eur"] = out["base_salary_fte_eur"] * out["fte"] + out["annual_bonus_eur"]
    out["labour_cost_eur"] = out["annual_pay_eur"] * (1 + out["employer_charges_rate"])
    return out


def headcount_summary(df: pd.DataFrame, date: str = "2025-12-31") -> dict:
    a = active_on(df, date)
    return {"headcount": int(len(a)), "fte": round(float(a["fte"].sum()), 1),
            "women_share_pct": round(100 * a["gender"].eq("F").mean(), 1)}


def headcount_by(df: pd.DataFrame, col: str, date: str = "2025-12-31") -> pd.DataFrame:
    a = active_on(df, date)
    t = a.groupby(col).agg(headcount=("employee_id", "count"), fte=("fte", "sum")).reset_index()
    t["fte"] = t["fte"].round(1)
    return t.sort_values("headcount", ascending=False).reset_index(drop=True)


def labour_cost_by(df: pd.DataFrame, col: str, date: str = "2025-12-31") -> pd.DataFrame:
    a = add_derived(active_on(df, date))
    t = a.groupby(col).agg(fte=("fte", "sum"), labour_cost_eur=("labour_cost_eur", "sum")).reset_index()
    t["cost_per_fte_eur"] = (t["labour_cost_eur"] / t["fte"]).round(0)
    t["labour_cost_eur"] = t["labour_cost_eur"].round(0)
    t["fte"] = t["fte"].round(1)
    return t.sort_values("labour_cost_eur", ascending=False).reset_index(drop=True)


def attrition(df: pd.DataFrame, year: int) -> dict:
    start, end = f"{year}-01-01", f"{year}-12-31"
    avg_hc = (len(active_on(df, start)) + len(active_on(df, end))) / 2
    leavers = df[(df["exit_date"] >= start) & (df["exit_date"] <= end)]
    vol = leavers["exit_reason"].eq("Resignation").sum()
    return {"year": year, "leavers": int(len(leavers)), "average_headcount": avg_hc,
            "attrition_rate_pct": round(100 * len(leavers) / avg_hc, 1),
            "voluntary_attrition_pct": round(100 * vol / avg_hc, 1)}


def gender_pay_gap(df: pd.DataFrame, date: str = "2025-12-31") -> dict:
    a = active_on(df, date)
    a = a[a["contract_type"] != "Apprentice"]  # apprentices have legal pay grids
    pay = a["base_salary_fte_eur"]
    men, women = pay[a["gender"].eq("M")].mean(), pay[a["gender"].eq("F")].mean()
    unadjusted = 100 * (men - women) / men
    rows = []
    for _, g in a.groupby(["job_level", "country"]):
        m, f = g[g["gender"].eq("M")], g[g["gender"].eq("F")]
        if len(m) >= MIN_GROUP and len(f) >= MIN_GROUP:
            rows.append((len(g), 100 * (m["base_salary_fte_eur"].mean() - f["base_salary_fte_eur"].mean()) / m["base_salary_fte_eur"].mean()))
    adjusted = sum(n * gap for n, gap in rows) / sum(n for n, _ in rows)
    return {"unadjusted_gap_pct": round(unadjusted, 1), "adjusted_gap_pct": round(adjusted, 1)}


def women_share_by_level(df: pd.DataFrame, date: str = "2025-12-31") -> pd.DataFrame:
    a = active_on(df, date)
    t = a.groupby("job_level").agg(headcount=("employee_id", "count"), women=("gender", lambda s: (s == "F").sum())).reset_index()
    t["women_share_pct"] = (100 * t["women"] / t["headcount"]).round(1)
    order = ["Operator", "Technician", "Professional", "Manager", "Senior Manager"]
    return t.set_index("job_level").loc[[o for o in order if o in t["job_level"].values]].reset_index()


def suppress_small_groups(t: pd.DataFrame, count_col: str = "headcount") -> pd.DataFrame:
    out = t.copy()
    mask = out[count_col] < MIN_GROUP
    for c in out.columns:
        if c != out.columns[0]:
            out[c] = out[c].astype(object)
            out.loc[mask, c] = "<5"
    return out
