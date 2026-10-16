"""Smoke tests for RetailPulse analytics; run with: python -m unittest discover -s tests"""
import unittest
import pandas as pd

from src.analytics import build_recommendations, prepare_dataset
from scripts.generate_demo_data import generate_demo_data


class RetailPulseTests(unittest.TestCase):
    def test_demo_dataset_is_500_rows(self):
        frame = generate_demo_data()
        self.assertEqual(len(frame), 500)
        self.assertIn("Product_Category", frame.columns)

    def test_sales_are_quantity_times_unit_price(self):
        source = pd.DataFrame({
            "Invoice ID": ["I-1", "I-2"],
            "Date": ["2026-03-01", "2026-03-02"],
            "Branch": ["A - Jaipur", "B - Delhi"],
            "Product": ["Cheese", "Milk"],
            "Product line": ["Dairy", "Dairy"],
            "Quantity": [2, 3],
            "Unit price": [100, 50],
            "Customer type": ["Member", "Normal"],
            "Payment": ["UPI", "Cash"],
            "Rating": [4.0, 5.0],
        })
        clean, _, audit = prepare_dataset(source)
        self.assertEqual(clean["Sales"].tolist(), [200.0, 150.0])
        self.assertEqual(audit["clean_rows"], 2)

    def test_invalid_quantity_is_removed_and_audited(self):
        source = pd.DataFrame({
            "Invoice_ID": ["I-1", "I-2"], "Date": ["2026-03-01", "2026-03-02"],
            "Branch": ["A", "B"], "Product": ["Cheese", "Milk"],
            "Product_Category": ["Dairy", "Dairy"], "Quantity": [1, -1],
            "Unit_Price": [100, 50], "Customer_Type": ["Member", "Normal"],
            "Payment_Method": ["UPI", "Cash"], "Rating": [4, 3],
        })
        clean, _, audit = prepare_dataset(source)
        self.assertEqual(len(clean), 1)
        self.assertEqual(audit["invalid_quantities"], 1)
        self.assertEqual(audit["removed_rows"], 1)

    def test_recommendations_return_for_valid_data(self):
        clean, _, _ = prepare_dataset(generate_demo_data(30))
        recs = build_recommendations(clean)
        self.assertGreaterEqual(len(recs), 4)
        self.assertIn("observation", recs[0])


if __name__ == "__main__":
    unittest.main()
