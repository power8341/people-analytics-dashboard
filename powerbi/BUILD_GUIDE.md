# Build the Power BI report (about 2 hours)

1. Run the pipeline (see README) so `data/hr_employees_clean.csv` exists.
2. Power BI Desktop > Get data > Text/CSV > `hr_employees_clean.csv`. In Power Query: set `hire_date` and `exit_date` to Date, `fte` and money columns to Decimal number, rename the query `Employees`, Close and Apply.
3. Create a date table: Modelling > New table:
   `Date = CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2025, 12, 31 ) )`, mark it as date table. No relationship is needed (the measures read the selected date).
4. Add the measures from `dax_measures.md`.
5. Build 4 pages, each with a date slicer (single date, default 31/12/2025) and slicers for country and department:
   - **Headcount and workforce structure**: cards (Headcount, FTE, Women Share %), bar by department, bar by country, column by age band, donut by contract type.
   - **Labour cost**: cards (Labour Cost, Labour Cost per FTE), bar of cost per FTE by department, table by country.
   - **Attrition**: card Attrition %, column of leavers by exit reason, table by department.
   - **Gender pay gap and equity**: card Gender Pay Gap %, clustered bar Avg Salary Men vs Women by job level, column Women Share % by job level.
6. Confidentiality: use `Headcount (confidential)` in tables so groups under 5 people are blank, and do not add employee-level tables.
7. Check the cards against `reports/kpi_summary.json` and `excel/people_kpis.xlsx`: they must match.
8. Save as `powerbi/people_analytics.pbix`, export each page as PNG to `powerbi/screenshots/` and add them to the README.
