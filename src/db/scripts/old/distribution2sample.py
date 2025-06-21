import json
import random
import csv
import calendar
from datetime import datetime, date, timedelta


# to run this    python  distribution2sample.py

def read_category_distribution(file_path: str) -> dict:
    """Read the category distribution JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        distribution = json.load(f)
    return distribution

def random_date_in_month(year: int, month: int) -> date:
    """Generate a random date within a given month and year."""
    first_day = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    random_day = random.randint(1, last_day)
    return date(year, month, random_day)

def generate_sample_dataset(distribution: dict, start_date: date, end_date: date, currency: str = "USD") -> list:
    """
    Generate a list of sample records for the period from start_date to end_date.
    
    For each month in the range and for each subcategory in the distribution,
    generate a random number of records between lower_monthly_freq and higher_monthly_freq.
    Each record gets a date, a random amount between lower_amount_limit and higher_amount_limit,
    a generated description, and the associated category and subcategory.
    
    Amounts for income subcategories ("Incoming P2P Transfers" -> "Incoming Money") remain positive,
    while amounts for any other categories are converted to negative values.
    """
    samples = []
    current = date(start_date.year, start_date.month, 1)
    
    while current <= end_date:
        year = current.year
        month = current.month

        # Iterate over all main categories and their subcategories in the distribution
        for cat, subcats in distribution.items():
            for subcat, limits in subcats.items():
                if not isinstance(limits, list) or len(limits) != 4:
                    # Skip if the limits are not correctly defined.
                    continue

                # Unpack the list:
                # [lower_monthly_freq, higher_monthly_freq, lower_amount_limit, higher_amount_limit]
                lower_freq, higher_freq, lower_amount, higher_amount = limits

                # For spending categories (i.e. not income), convert the amount limits to negative.
                # We assume that only "Incoming P2P Transfers" with subcategory "Incoming Money" remains positive.
                if not (cat == "Incoming P2P Transfers" and subcat == "Incoming Money"):
                    # The original lower_amount < higher_amount (in absolute terms).
                    # Convert them to spending amounts:
                    #   New lower bound = -1 * (higher_amount)
                    #   New upper bound = -1 * (lower_amount)
                    lower_amount, higher_amount = -float(higher_amount), -float(lower_amount)
                else:
                    lower_amount, higher_amount = float(lower_amount), float(higher_amount)

                # Determine how many records to generate this month for this subcategory
                if higher_freq > lower_freq:
                    record_count = random.randint(lower_freq, higher_freq)
                else:
                    record_count = lower_freq

                for _ in range(record_count):
                    # Generate a random date within the current month
                    record_date = random_date_in_month(year, month)
                    # Generate a random amount within the specified limits.
                    # Note: For spending, this will be a negative value.
                    amount = round(random.uniform(lower_amount, higher_amount), 2)
                    # Create a simple description.
                    description = f"Simulated expense for {cat} - {subcat}"
                    # Append record to the sample list.
                    samples.append({
                        "date": record_date.isoformat(),
                        "desc": description,
                        "amount": amount,
                        "currency": currency,
                        "cat": cat,
                        "subcat": subcat
                    })
        
        # Move to the first day of the next month.
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)
    
    return samples

def write_to_csv(records: list, output_file: str):
    """Write the list of records to a CSV file."""
    fieldnames = ["date", "desc", "amount", "currency", "cat", "subcat"]
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

if __name__ == "__main__":
    # Define the path to your JSON distribution file
    distribution_file = "./category_sample_distribution.json"  # Adjust path as needed
    # Read the distribution
    distribution = read_category_distribution(distribution_file)
    print("Distribution read:")
    print(json.dumps(distribution, indent=2))
    
    # Set the start and end dates for the sample data generation
    start_date = datetime.strptime("2024-01-01", "%Y-%m-%d").date()
    end_date = datetime.strptime("2025-04-30", "%Y-%m-%d").date()
    print("Starting generation...")
    # Generate sample dataset (using USD as the currency by default)
    samples = generate_sample_dataset(distribution, start_date, end_date, currency="USD")
    
    # Write the generated dataset to a CSV file
    output_csv = "sample_dataset.csv"
    write_to_csv(samples, output_csv)
    
    print(f"Sample dataset with {len(samples)} records written to {output_csv}")
