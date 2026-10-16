# RetailPulse — Supermarket Sales Intelligence Dashboard

RetailPulse is an interactive Python dashboard for analyzing supermarket transactions and translating data into practical business actions. It follows the course capstone workflow: data audit and cleansing, metric engineering (`Sales = Quantity × Unit_Price`), aggregation, visualization, and executive recommendations.

> **Important data note:** `data/supermarket_sales.csv` contains 500 **synthetic demo transactions** created for this project. It is not the official class dataset and should not be cited as real findings. Upload the official course CSV in the sidebar before preparing final figures for submission.

## Features

- Interactive overview with sales, transaction count, average basket value and average rating.
- Date, branch, product category and customer-type filters.
- Weekly sales trend, branch comparisons, category performance and top products.
- Customer-type basket comparison, payment mix and rating distribution.
- Data-quality audit for missing fields, duplicate invoice IDs, invalid dates, quantities and prices.
- Rule-based decision assistant that distinguishes measured observations from suggested actions.
- Searchable transaction explorer and filtered CSV export.
- CSV column alias handling for common names such as `Invoice ID`, `Product line`, `Unit price`, `Customer type` and `Payment`.
- Responsive Streamlit layout and deterministic demo-data generator.

## Project structure

```text
retailpulse_project/
├── app.py                         # Streamlit UI and charts
├── requirements.txt               # Runtime dependencies
├── README.md                      # Setup and usage guide
├── data/
│   └── supermarket_sales.csv      # 500 synthetic demo transactions
├── src/
│   └── analytics.py               # Validation, cleaning, metrics and recommendations
├── scripts/
│   └── generate_demo_data.py      # Re-create demo CSV
└── tests/
    └── test_analytics.py          # Smoke tests
```

## Run locally

Python 3.10–3.12 is recommended.

### Windows (PowerShell)

```powershell
cd retailpulse_project
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
cd retailpulse_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The app normally opens at `http://localhost:8501`.

## Use the official dataset

1. Export/download your class supermarket sales worksheet as a CSV file.
2. Run the app and use **Upload your sales CSV** in the sidebar.
3. Required fields are invoice ID, date, branch, product, product category/line, quantity and unit price. The loader recognizes common heading variants.
4. Inspect the **Data Quality** tab before interpreting dashboard results.
5. Report findings from the real uploaded data, not from the synthetic demo dataset.

The official class workbook describes sales as quantity multiplied by unit price. For transparency, RetailPulse recomputes this metric instead of trusting an existing sales total column.

## Re-create the sample data

```bash
python scripts/generate_demo_data.py
```

The script uses a fixed random seed, so the demo dataset is reproducible.

## Run checks

```bash
python -m unittest discover -s tests -v
```

## Publish to GitHub

Create an empty repository on GitHub, then run these commands from this project directory:

```bash
git init
git add .
git commit -m "Build RetailPulse sales analytics dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/retailpulse-project.git
git push -u origin main
```

Replace the URL with your repository's actual URL. Do not upload private/customer data or credentials.

## Deployment options

For a quick hosted demo, deploy to Streamlit Community Cloud by connecting the GitHub repository, choosing `app.py` as the main file, and allowing it to install `requirements.txt`. Always verify current provider limits and privacy rules before uploading the official dataset.

## Analytical limitations

- The included dataset is fictional and intended only to demonstrate application behavior.
- The decision assistant is a transparent rule-based summary, not a trained AI/ML prediction model.
- Sales are gross sales as `Quantity × Unit_Price`; costs and profit are not inferred where no cost data exists.
- Data patterns show associations, not causation. Validate hypotheses before changing stock or marketing policies.
