# this is db/scrips/sample_generator.py

# the input is categories and start_date , end_date

# the output is csv file with these columns 

# date, desc amount, currency, cat, subcat, 

# this function will use LLMService logic to generate sample records 

# the challange is this: if we generate record samples day by day, then we wont be able to control the distrubition of the categories 
# and overall data wont make sense. 
# 
# if we generate in bulk for example month per month then it might makes sense. but not all months should be same
 

import csv
import random
from datetime import datetime, timedelta
from calendar import monthrange
from llm_service import generate_description  # hypothetical function

def generate_monthly_records(start_date, end_date, category_distribution, total_records):
    records = []
    # Get number of days in month
    days_in_month = monthrange(start_date.year, start_date.month)[1]
    
    for _ in range(total_records):
        # Random date in the month
        random_day = random.randint(1, days_in_month)
        record_date = datetime(start_date.year, start_date.month, random_day)
        
        # Choose category based on weighted distribution
        category = random.choices(
            population=list(category_distribution.keys()),
            weights=list(category_distribution.values()),
            k=1
        )[0]
        
        # Assume subcategories are a list for the chosen category
        subcategory = random.choice(category_distribution[category]["subcategories"])
        
        # Generate description using LLMService
        description = generate_description(category, subcategory)
        
        # Generate amount (simulate realistic values)
        amount = round(random.uniform(10.0, 500.0), 2)
        
        # Set currency (for example, based on country)
        currency = "USD"
        
        records.append({
            "date": record_date.strftime("%Y-%m-%d"),
            "desc": description,
            "amount": amount,
            "currency": currency,
            "cat": category,
            "subcat": subcategory,
        })
    
    return records

def generate_sample_csv(start_date, end_date, category_distribution, output_file):
    current_date = start_date
    all_records = []
    
    while current_date <= end_date:
        # Determine number of records for the month, e.g., random between 50 and 150
        total_records = random.randint(50, 150)
        
        # Generate records for the current month
        month_records = generate_monthly_records(current_date, current_date, category_distribution, total_records)
        all_records.extend(month_records)
        
        # Move to next month
        next_month = current_date.month % 12 + 1
        next_year = current_date.year + (1 if current_date.month == 12 else 0)
        current_date = datetime(next_year, next_month, 1)
    
    # Write all records to CSV
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["date", "desc", "amount", "currency", "cat", "subcat"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rec in all_records:
            writer.writerow(rec)

# Example category distribution (this can be dynamically generated)

categories_yaml_path='assets/config/categories.yaml'

# read the categories yaml

category_distribution = {
    "Food & Dining": {"weight": 30, "subcategories": ["Groceries", "Restaurants", "Coffee", "Takeout"]},
    "Transportation": {"weight": 20, "subcategories": ["Fuel", "Taxi", "Public Transportation"]},
    # add more categories...
}

category_distribution = {
    "Food & Dining": {"freq_weight": 30, "subcategories": ["Groceries", "Restaurants", "Coffee", "Takeout"]},
    "Transportation": {"weight": 20, "subcategories": ["Fuel", "Taxi", "Public Transportation"]},
    # add more categories...
}

# i must be able to state "Food & Dining" 's freq_weight and i want to be also state subcategories freq weigjt 
# and avg_amount_weight 

# Adjust weights: extract weights and subcategories separately for random.choices
adjusted_distribution = {k: {"weight": v["weight"], "subcategories": v["subcategories"]} for k, v in category_distribution.items()}
weights = [v["weight"] for v in adjusted_distribution.values()]
pop = list(adjusted_distribution.keys())
for key in adjusted_distribution:
    adjusted_distribution[key] = {"subcategories": adjusted_distribution[key]["subcategories"]}

# Example usage
generate_sample_csv(datetime(2024, 1, 1), datetime(2024, 12, 31), category_distribution, "sample_data.csv")
