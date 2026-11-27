"""Reproduce synthetic e-commerce sales analysis. Run from any directory."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ["Electronics", "Fashion", "Home", "Books"]

def generate_orders():
    """One row per completed order. USD is an illustrative currency."""
    rng = np.random.default_rng(73)
    n = 2400
    customer_weights = rng.lognormal(0, .8, 300)
    customer_weights /= customer_weights.sum()
    dates = pd.date_range("2025-01-01", "2025-12-31")
    seasonal_weights = np.where(dates.month >= 10, 1.45, 1.0)
    seasonal_weights /= seasonal_weights.sum()
    category = rng.choice(CATEGORIES, n, p=[.28,.34,.23,.15])
    price_scale = pd.Series(category).map(dict(zip(CATEGORIES,[110,45,65,18]))).to_numpy()
    return pd.DataFrame({
        "order_id": np.arange(1,n+1),
        "order_date": rng.choice(dates,n,p=seasonal_weights),
        "customer_id": rng.choice(np.arange(1,301),n,p=customer_weights),
        "category": category,
        "amount": np.round(rng.gamma(2,price_scale),2)
    }).sort_values(["order_date","order_id"]).reset_index(drop=True)

def prepare(orders):
    df = orders.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="raise")
    assert df.shape[0] == 2400
    assert not df.isna().any().any()
    assert df["order_id"].is_unique
    assert df["amount"].gt(0).all()
    df["month"] = df.order_date.dt.to_period("M").astype(str)
    df["weekday"] = df.order_date.dt.day_name()
    df["quarter"] = "Q" + df.order_date.dt.quarter.astype(str)
    return df

def analyze(df):
    monthly = df.groupby("month").agg(revenue=("amount","sum"), orders=("order_id","count"))
    monthly["growth_pct"] = monthly.revenue.pct_change(fill_method=None) * 100
    monthly["average_order_value"] = monthly.revenue / monthly.orders
    categories = df.groupby("category").amount.agg(["sum","mean","count"]).sort_values("sum",ascending=False)
    categories.columns = ["revenue","average_order_value","orders"]
    categories["revenue_share_pct"] = categories.revenue / df.amount.sum() * 100
    pivot = df.pivot_table(index="month",columns="category",values="amount",aggfunc="sum",fill_value=0)
    spend = df.groupby("customer_id").agg(spend=("amount","sum"),orders=("order_id","count"))
    spend = spend.sort_values(["spend"],ascending=False).reset_index()
    spend["cumulative_revenue_pct"] = spend.spend.cumsum()/spend.spend.sum()*100
    spend["customer_pct"] = np.arange(1,len(spend)+1)/len(spend)*100
    return monthly,categories,pivot,spend

def main():
    for folder in ["data","reports","visualizations"]: (ROOT/folder).mkdir(exist_ok=True)
    raw = generate_orders()
    raw.to_csv(ROOT/"data/orders.csv",index=False)
    df = prepare(pd.read_csv(ROOT/"data/orders.csv"))
    df.to_csv(ROOT/"data/orders_enriched.csv",index=False)
    monthly,categories,pivot,spend = analyze(df)
    for name,table in [("monthly_trend",monthly),("category_summary",categories),("month_category_pivot",pivot),("customer_spend",spend)]:
        table.to_csv(ROOT/f"reports/{name}.csv",index=name!="customer_spend")
    assert np.isclose(monthly.revenue.sum(),df.amount.sum())
    assert np.isclose(pivot.to_numpy().sum(),df.amount.sum())
    assert categories.orders.sum() == len(df)
    k = math.ceil(len(spend)*.10)
    top_share = spend.head(k).spend.sum()/spend.spend.sum()*100
    top20 = spend.head(math.ceil(len(spend)*.20)).spend.sum()/spend.spend.sum()*100
    best,worst = monthly.revenue.idxmax(),monthly.revenue.idxmin()
    lead = categories.index[0]
    findings = [
        f"Revenue totals USD {df.amount.sum():,.2f} across {len(df):,} orders and {len(spend)} purchasing customers.",
        f"The best month is {best} at USD {monthly.loc[best,'revenue']:,.2f}. The lowest is {worst} at USD {monthly.loc[worst,'revenue']:,.2f}.",
        f"{lead} contributes {categories.loc[lead,'revenue_share_pct']:.1f}% of revenue with an average order value of USD {categories.loc[lead,'average_order_value']:.2f}.",
        f"The top {k} of {len(spend)} customers ({k/len(spend)*100:.1f}%) contribute {top_share:.1f}% of revenue. The top 20% rounded up contribute {top20:.1f}%."
    ]
    actions = [
        f"Pilot a loyalty offer for the top {k} customers, who account for {top_share:.1f}% of revenue. Compare repeat purchase rate and margin with a holdout group.",
        f"Prioritize availability checks for {lead}, which generates {categories.loc[lead,'revenue_share_pct']:.1f}% of revenue. Track stockouts before increasing purchasing budgets.",
        f"Review the {worst} sales funnel, where revenue was USD {monthly.loc[worst,'revenue']:,.2f}, against {best} at USD {monthly.loc[best,'revenue']:,.2f}. Compare traffic, conversion and promotion costs before testing a campaign."
    ]
    sns.set_theme(style="whitegrid")
    def draw(ax,kind):
        if kind == "monthly_revenue":
            ax.plot(monthly.index,monthly.revenue,marker="o",color="#0072B2")
            for month,color in [(best,"#009E73"),(worst,"#D55E00")]:
                ax.scatter(month,monthly.loc[month,"revenue"],color=color,s=80,zorder=3)
                ax.annotate(month, (month,monthly.loc[month,"revenue"]),xytext=(0,10),textcoords="offset points",ha="center",fontsize=8)
            ax.set(title="Monthly revenue with best and lowest months",ylabel="Revenue (USD)",xlabel="Month")
            ax.tick_params(axis="x",rotation=45)
        elif kind == "monthly_growth":
            ax.bar(monthly.index[1:],monthly.growth_pct.iloc[1:],color="#0072B2")
            ax.axhline(0,color="black",lw=.8)
            ax.set(title="Month over month revenue growth",ylabel="Growth (%)",xlabel="Month")
            ax.tick_params(axis="x",rotation=45)
        elif kind == "category_revenue":
            ax.bar(categories.index,categories.revenue,color=["#0072B2","#E69F00","#CC79A7","#56B4E9"])
            ax.set(title=f"{lead} leads category revenue",ylabel="Revenue (USD)",xlabel="Category",ylim=(0,categories.revenue.max()*1.15))
        elif kind == "category_heatmap":
            sns.heatmap(pivot,ax=ax,cmap="Blues",annot=True,fmt=".0f",cbar_kws={"label":"Revenue (USD)"})
            ax.set(title="Monthly revenue by category",xlabel="Category",ylabel="Month")
        else:
            ax.plot(spend.customer_pct,spend.cumulative_revenue_pct,color="#0072B2")
            ax.scatter(k/len(spend)*100,top_share,color="#D55E00",zorder=3)
            ax.axhline(80,color="gray",ls="--",label="80% revenue reference")
            ax.set(title=f"Top 10% of customers generate {top_share:.1f}% of revenue",xlabel="Customers ranked by spend (%)",ylabel="Cumulative revenue (%)",xlim=(0,100),ylim=(0,100))
            ax.legend()
    kinds=["monthly_revenue","monthly_growth","category_revenue","category_heatmap","customer_pareto"]
    for kind in kinds:
        fig,ax=plt.subplots(figsize=(10,6))
        draw(ax,kind)
        fig.tight_layout()
        fig.savefig(ROOT/f"visualizations/{kind}.png",dpi=150)
        plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(16,11))
    for ax,kind in zip(axes.flat,["monthly_revenue","monthly_growth","category_revenue","customer_pareto"]): draw(ax,kind)
    fig.suptitle("Sales performance | Simulated 2025 orders",fontsize=20)
    fig.tight_layout(rect=(0,0,1,.96))
    fig.savefig(ROOT/"visualizations/dashboard.png",dpi=150)
    plt.close(fig)
    styles=getSampleStyleSheet()
    styles["BodyText"].fontSize=10
    styles["BodyText"].leading=14
    story=[Paragraph("Sales Trend Analysis",styles["Title"])]
    sections=[
        ("Context",["A practice analysis of 2,400 simulated completed e-commerce orders during calendar year 2025. A manager wants to understand revenue trends, categories and customer concentration. Amounts are illustrative USD gross sales."]),
        ("Key findings",findings),
        ("Recommendations",actions),
        ("Next steps",["Validate these patterns against real order, traffic, stock and margin data before a business rollout. The generator deliberately adds Q4 seasonality, customer spending concentration and category price differences. Results are practice findings, with no measured causal effect or profit estimate."])]
    for heading,paragraphs in sections:
        story.append(Paragraph(heading,styles["Heading2"]))
        for para in paragraphs:
            story.append(Paragraph(para,styles["BodyText"]))
            story.append(Spacer(1,5))
    SimpleDocTemplate(str(ROOT/"reports/business_brief.pdf"),rightMargin=45,leftMargin=45,topMargin=35,bottomMargin=35).build(story)
    readme = """# Sales Trend Analysis

InternCircle Project 03 explores revenue trends, category performance and customer concentration using reproducible simulated e-commerce orders.

## Business questions

Which months and categories earn most? Who are the most valuable customers? What actions should a manager test?

## Data and assumptions

The data generator uses seed 73 and creates 2,400 completed orders in calendar year 2025. Each row represents one order assigned to one category. USD is an illustrative currency. Customer selection weights are unequal, Q4 order probability is elevated and categories have different amount distributions. No personal data is used. This is simulated data. Revenue is gross order value, with no returns, discounts, tax, cost or margin model. Customer concentration uses observed purchasing customers and rounds the top group size up. January growth is undefined because December 2024 is unavailable. This project follows the guide's sales analysis workflow. Churn labels and a churn model are outside this dataset.

## Measured findings

""" + "\n".join("- "+f for f in findings) + """

## Recommended actions

""" + "\n".join("- "+a for a in actions) + """

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
"""
    (ROOT/"README.md").write_text(readme,encoding="utf-8")
    print("\n".join(findings))
    print(monthly.round(2).to_string())
    return df,monthly,categories,pivot,spend

if __name__=="__main__":
    main()
