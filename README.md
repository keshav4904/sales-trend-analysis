# Sales Trend Analysis

InternCircle Project 03 explores revenue trends, category performance and customer concentration using reproducible simulated e-commerce orders.

## Business questions

Which months and categories earn most? Who are the most valuable customers? What actions should a manager test?

## Data and assumptions

The data generator uses seed 73 and creates 2,400 completed orders in calendar year 2025. Each row represents one order assigned to one category. USD is an illustrative currency. Customer selection weights are unequal, Q4 order probability is elevated and categories have different amount distributions. No personal data is used. This is simulated data. Revenue is gross order value, with no returns, discounts, tax, cost or margin model. Customer concentration uses observed purchasing customers and rounds the top group size up. January growth is undefined because December 2024 is unavailable. This project follows the guide's sales analysis workflow. Churn labels and a churn model are outside this dataset.

## Measured findings

- Revenue totals USD 301,824.03 across 2,400 orders and 281 purchasing customers.
- The best month is 2025-12 at USD 37,248.74. The lowest is 2025-02 at USD 17,731.01.
- Electronics contributes 46.8% of revenue with an average order value of USD 212.27.
- The top 29 of 281 customers (10.3%) contribute 36.8% of revenue. The top 20% rounded up contribute 55.8%.

## Recommended actions

- Pilot a loyalty offer for the top 29 customers, who account for 36.8% of revenue. Compare repeat purchase rate and margin with a holdout group.
- Prioritize availability checks for Electronics, which generates 46.8% of revenue. Track stockouts before increasing purchasing budgets.
- Review the 2025-02 sales funnel, where revenue was USD 17,731.01, against 2025-12 at USD 37,248.74. Compare traffic, conversion and promotion costs before testing a campaign.

## Reproduce

Use Python 3.10 or later, then run from the repository folder.

    python -m pip install -r requirements.txt
    python src/analyze.py
    jupyter notebook notebooks/sales_analysis.ipynb

The script reads back the generated raw CSV, validates order identifiers, missing values and positive amounts, extracts month, weekday and quarter, and produces CSV summaries, five charts, a dashboard and a one-page PDF business brief.

## Files

- data/orders.csv and orders_enriched.csv
- notebooks/sales_analysis.ipynb with executed outputs
- src/analyze.py
- reports/ with monthly growth, category summary, month-category pivot, customer spend and business brief
- visualizations/ with five charts and dashboard

![Sales dashboard](visualizations/dashboard.png)

## Interpretation

The top-customer calculation tests the Pareto idea against the actual generated figures. Concentration does not automatically equal an 80/20 split. Recommendations are proposed experiments. Repeating the same seed and dependency versions reproduces the figures.
