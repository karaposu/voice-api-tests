from pydantic import BaseModel, Field
from typing import List

class SubcategoryDistribution(BaseModel):
    """
    Distribution settings for a subcategory.
    
    Attributes:
      - name: The subcategory name.
      - lower_monthly_freq: Minimum expected monthly transaction frequency.
      - higher_monthly_freq: Maximum expected monthly transaction frequency.
      - lower_amount_limit: Minimum expected transaction amount.
      - higher_amount_limit: Maximum expected transaction amount.
    """
    name: str = Field(..., description="The subcategory name")
    lower_monthly_freq: int = Field(..., description="Minimum expected monthly frequency")
    higher_monthly_freq: int = Field(..., description="Maximum expected monthly frequency")
    lower_amount_limit: float = Field(..., description="Minimum expected transaction amount")
    higher_amount_limit: float = Field(..., description="Maximum expected transaction amount")

class CategoryDistribution(BaseModel):
    """
    Distribution settings for a main category.
    
    Attributes:
      - category: The main category name.
      - subcategories: A list of subcategory distribution settings.
    """
    category: str = Field(..., description="The main category name")
    subcategories: List[SubcategoryDistribution] = Field(
        ..., description="List of subcategory distribution settings"
    )

class OverallCategoryDistribution(BaseModel):
    """
    Container for all category distributions.
    
    Attributes:
      - categories: A list of main category distributions.
    """
    categories: List[CategoryDistribution] = Field(
        ..., description="List of all category distributions"


    )


def create_overall_category_distribution(
    distribution_data: Dict[str, Dict[str, List[Union[int, float]]]]
) -> OverallCategoryDistribution:
    """
    Given a nested dictionary representing category distribution settings,
    create and return an OverallCategoryDistribution object.
    
    The expected format for distribution_data is:
    
    {
        "Main Category Name": {
            "Subcategory Name": [lower_monthly_freq, higher_monthly_freq, lower_amount_limit, higher_amount_limit],
            ...
        },
        ...
    }
    
    If a subcategory's list is empty or not of length 4, it will be skipped.
    """
    category_objs = []
    for main_cat, subcats in distribution_data.items():
        subcat_objs = []
        # subcats should be a dictionary where keys are subcategory names
        for subcat_name, values in subcats.items():
            # Validate that values is a list of exactly 4 items
            if isinstance(values, list) and len(values) == 4:
                try:
                    subcat_obj = SubcategoryDistribution(
                        name=subcat_name,
                        lower_monthly_freq=int(values[0]),
                        higher_monthly_freq=int(values[1]),
                        lower_amount_limit=float(values[2]),
                        higher_amount_limit=float(values[3]),
                    )
                    subcat_objs.append(subcat_obj)
                except Exception as e:
                    # You can log or handle errors for this subcategory if needed.
                    print(f"Skipping subcategory {subcat_name} due to error: {e}")
            else:
                # Skip if the list is empty or has an invalid number of elements.
                print(f"Skipping subcategory {subcat_name} due to invalid value list: {values}")
        if subcat_objs:
            cat_obj = CategoryDistribution(
                category=main_cat,
                subcategories=subcat_objs
            )
            category_objs.append(cat_obj)
    overall = OverallCategoryDistribution(categories=category_objs)
    return overall



# Example usage:
if __name__ == "__main__":
    distribution_data = {
        "Food & Dining": {
            "Groceries": [4, 8, 10, 150],
            "Restaurants": [2, 6, 15, 200],
            "Coffee": [0, 5, 2, 15],
            "Takeout": [1, 4, 8, 50]
        },
        "Transportation": {
            "Fuel": [1, 5, 20, 100],
            "Taxi": [0, 3, 5, 40],
            "Public Transportation": [0, 10, 1, 15]
        },
        "Utilities": {
            "Electricity and Water and Gas": [0, 2, 50, 300],
            "Internet and Mobile": [0, 1, 20, 80]
        }
    }

    overall_dist = create_overall_category_distribution(distribution_data)
    print(overall_dist.json(indent=2))

# Example usage:
example_distribution = OverallCategoryDistribution(
    categories=[
        CategoryDistribution(
            category="Food & Dining",
            subcategories=[
                SubcategoryDistribution(
                    name="Groceries",
                    lower_monthly_freq=4,
                    higher_monthly_freq=8,
                    lower_amount_limit=10.0,
                    higher_amount_limit=150.0,
                ),
                SubcategoryDistribution(
                    name="Restaurants",
                    lower_monthly_freq=2,
                    higher_monthly_freq=6,
                    lower_amount_limit=15.0,
                    higher_amount_limit=200.0,
                ),
                SubcategoryDistribution(
                    name="Coffee",
                    lower_monthly_freq=0,
                    higher_monthly_freq=5,
                    lower_amount_limit=2.0,
                    higher_amount_limit=15.0,
                ),
                SubcategoryDistribution(
                    name="Takeout",
                    lower_monthly_freq=1,
                    higher_monthly_freq=4,
                    lower_amount_limit=8.0,
                    higher_amount_limit=50.0,
                ),
            ],
        ),
        CategoryDistribution(
            category="Transportation",
            subcategories=[
                SubcategoryDistribution(
                    name="Fuel",
                    lower_monthly_freq=1,
                    higher_monthly_freq=5,
                    lower_amount_limit=20.0,
                    higher_amount_limit=100.0,
                ),
                SubcategoryDistribution(
                    name="Taxi",
                    lower_monthly_freq=0,
                    higher_monthly_freq=3,
                    lower_amount_limit=5.0,
                    higher_amount_limit=40.0,
                ),
                SubcategoryDistribution(
                    name="Public Transportation",
                    lower_monthly_freq=0,
                    higher_monthly_freq=10,
                    lower_amount_limit=1.0,
                    higher_amount_limit=15.0,
                ),
            ],
        ),
        CategoryDistribution(
            category="Utilities",
            subcategories=[
                SubcategoryDistribution(
                    name="Electricity and Water and Gas",
                    lower_monthly_freq=0,  # Expecting that sometimes no bill is paid.
                    higher_monthly_freq=2,
                    lower_amount_limit=50.0,
                    higher_amount_limit=300.0,
                ),
                SubcategoryDistribution(
                    name="Internet and Mobile",
                    lower_monthly_freq=0,
                    higher_monthly_freq=1,
                    lower_amount_limit=20.0,
                    higher_amount_limit=80.0,
                ),
            ],
        ),
        # ... add more categories as needed
    ]
)

# To see the JSON representation:
print(example_distribution.json(indent=2))
