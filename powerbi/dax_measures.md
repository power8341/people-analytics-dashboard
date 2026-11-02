# DAX measures

Table name: `Employees` (loaded from `data/hr_employees_clean.csv`). A `Date` table is used for the "as of" date.

```DAX
As Of Date = MAX ( 'Date'[Date] )

Headcount =
VAR d = [As Of Date]
RETURN
    CALCULATE (
        COUNTROWS ( Employees ),
        Employees[hire_date] <= d,
        OR ( ISBLANK ( Employees[exit_date] ), Employees[exit_date] > d )
    )

FTE =
VAR d = [As Of Date]
RETURN
    CALCULATE (
        SUM ( Employees[fte] ),
        Employees[hire_date] <= d,
        OR ( ISBLANK ( Employees[exit_date] ), Employees[exit_date] > d )
    )

Labour Cost =
VAR d = [As Of Date]
RETURN
    CALCULATE (
        SUM ( Employees[labour_cost_eur] ),
        Employees[hire_date] <= d,
        OR ( ISBLANK ( Employees[exit_date] ), Employees[exit_date] > d )
    )

Labour Cost per FTE = DIVIDE ( [Labour Cost], [FTE] )

Leavers =
VAR y = YEAR ( [As Of Date] )
RETURN
    CALCULATE (
        COUNTROWS ( Employees ),
        YEAR ( Employees[exit_date] ) = y
    )

Average Headcount =
VAR y = YEAR ( [As Of Date] )
VAR hcStart = CALCULATE ( [Headcount], 'Date'[Date] = DATE ( y, 1, 1 ) )
VAR hcEnd   = CALCULATE ( [Headcount], 'Date'[Date] = DATE ( y, 12, 31 ) )
RETURN DIVIDE ( hcStart + hcEnd, 2 )

Attrition % = DIVIDE ( [Leavers], [Average Headcount] )

Women Share % = DIVIDE ( CALCULATE ( [Headcount], Employees[gender] = "F" ), [Headcount] )

Avg Salary Men =
CALCULATE ( AVERAGE ( Employees[base_salary_fte_eur] ), Employees[gender] = "M", Employees[contract_type] <> "Apprentice" )

Avg Salary Women =
CALCULATE ( AVERAGE ( Employees[base_salary_fte_eur] ), Employees[gender] = "F", Employees[contract_type] <> "Apprentice" )

Gender Pay Gap % = DIVIDE ( [Avg Salary Men] - [Avg Salary Women], [Avg Salary Men] )

Headcount (confidential) = IF ( [Headcount] < 5, BLANK (), [Headcount] )
```

Expected values on 31 Dec 2025 (same as the Python pipeline and the Excel file): headcount 1,217, FTE 1,165.6, unadjusted gender pay gap 2.7%, attrition 2025 10.3%.
