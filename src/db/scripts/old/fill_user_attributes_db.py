# To run this: 
#   python -m db.scripts.fill_user_attributes_db

import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.user import User
from db.models.user_attributes import UserAttributes


def random_bool():
    """Return a random True/False value."""
    return bool(random.getrandbits(1))

def random_choice(choices):
    """Convenience function to pick a random item from a list."""
    return random.choice(choices)

def fill_random_user_attributes(session, user_id=0):
    """
    Fills (or updates) the UserAttributes row for the given user_id with random values.
    If the row doesn't exist, it creates it first.
    """
    # 1. Verify the user actually exists.
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        print(f"[ERROR] No user found with user_id={user_id}. Cannot fill attributes.")
        return
    
    # 2. Check if a UserAttributes record already exists for this user.
    attributes = session.query(UserAttributes).filter_by(user_id=user_id).first()
    if attributes:
        print(f"[INFO] UserAttributes already exist for user_id={user_id}; will update them randomly.")
    else:
        attributes = UserAttributes(user_id=user_id)
        session.add(attributes)
        session.commit()
        print(f"[INFO] Created new UserAttributes row for user_id={user_id}. Now populating with random values.")

    # 3. Populate random “legit” values.
    # -----------------------------------------------------------------------
    # Basic Demographics
    # -----------------------------------------------------------------------
    attributes.gender = random_choice(["Male", "Female"])
    attributes.country_code = random_choice(["TR", "US", "DE", "FR", "NL"])
    attributes.city_name = random_choice(["Istanbul", "New York", "Berlin", "Paris", "Amsterdam"])
    attributes.marital_status = random_choice(["single", "married", "divorced"])
    attributes.kids = random_choice(["none", "1", "2", "3+"])
    attributes.kids_in_same_household = random_choice(["yes", "no"])
    attributes.educational_level = random_choice([
        "primary_school_finished",
        "highschool_finished",
        "still_in_highschool",
        "still_studying_bachelor",
        "master_finished",
        "still_studying_masters",
        "still_studying_phd",
        "phd_finished"
    ])
    attributes.housing_status = random_choice(["own", "rent"])
    
    # vehicle ownership
    attributes.vehicle_ownership = random_choice(["yes", "no"])
    if attributes.vehicle_ownership == "yes":
        attributes.vehicle_type = random_choice(["dizel", "electric", "motorcycle"])
    else:
        attributes.vehicle_type = None
    
    attributes.source_of_income = random_choice(["work", "family_and_work", "family"])

    # -----------------------------------------------------------------------
    # Food Attributes
    # -----------------------------------------------------------------------
    attributes.food_type_preference = random_choice(["Vegetarian","Kebab lover","Salad lover","Eats all"])
    
    # Booleans for dietary restrictions
    attributes.dietary_gluten_free = random_bool()
    attributes.dietary_lactose_intolerant = random_bool()
    attributes.dietary_vegan = random_bool()
    attributes.dietary_pescatarian = random_bool()
    attributes.dietary_kosher = random_bool()
    attributes.dietary_halal = random_bool()
    attributes.dietary_nut_allergy = random_bool()
    attributes.dietary_low_carb = random_bool()
    attributes.dietary_sugar_free = random_bool()
    
    attributes.spice_tolerance = random_choice(["Mild","Medium","Spicy","Extra spicy"])
    attributes.preferred_meal_time = random_choice([
        "Early riser (6-7 AM)",
        "Late breakfast (10-11 AM)",
        "Early lunch (11 AM - 12 PM)",
        "Late lunch (1-2 PM)",
        "Early dinner (5-6 PM)",
        "Late dinner (8-9 PM)",
        "Midnight snacker"
    ])
    
    # Beverage booleans
    attributes.beverage_coffee_lover = random_bool()
    attributes.beverage_tea_enthusiast = random_bool()
    attributes.beverage_juice_drinker = random_bool()
    attributes.beverage_water_only = random_bool()
    attributes.beverage_soda_drinker = random_bool()
    attributes.beverage_alcoholic = random_bool()
    attributes.beverage_smoothie_lover = random_bool()

    # EatingHabits
    attributes.eating_speed = random_choice(["Fast eater","Moderate eater","Slow eater"])
    attributes.meal_portion_size = random_choice(["Small","Regular","Large","Extra-large"])

    # CookingSkills
    attributes.cooking_skill_level = random_choice(["Beginner","Intermediate","Advanced","Professional chef"])
    attributes.favorite_cooking_method = random_choice([
        "Grilling","Baking","Frying","Steaming","Boiling","Slow cooking","Raw preparation (e.g., salads)"
    ])

    attributes.food_adventurousness = random_choice([
        "Adventurous eater (tries anything)",
        "Cautious eater (tries new foods occasionally)",
        "Picky eater (prefers familiar foods)"
    ])
    attributes.sweet_tooth = random_choice([
        "Loves sweets (eats dessert daily)",
        "Moderate sweet tooth (enjoys dessert occasionally)",
        "Rarely eats sweets"
    ])

    # FavoriteFruits
    attributes.fruit_apples = random_bool()
    attributes.fruit_bananas = random_bool()
    attributes.fruit_berries = random_bool()
    attributes.fruit_citrus = random_bool()
    attributes.fruit_grapes = random_bool()
    attributes.fruit_mangoes = random_bool()
    attributes.fruit_melons = random_bool()

    attributes.dining_out_frequency = random_choice([
        "Daily","A few times a week","Once a week","A few times a month","Rarely"
    ])
    attributes.breakfast_habits = random_choice([
        "Cereal","Eggs","Toast","Smoothie","No breakfast","Full English breakfast","Cheese, tomatoes, olives"
    ])
    
    # FoodEthics
    attributes.ethics_organic_only = random_bool()
    attributes.ethics_fair_trade = random_bool()
    attributes.ethics_local_produce = random_bool()
    attributes.ethics_sustainable_seafood = random_bool()
    attributes.ethics_cruelty_free = random_bool()

    attributes.snack_frequency = random_choice([
        "Constantly snacking","A few times a day","Once a day","Rarely"
    ])
    attributes.food_texture_preference = random_choice(["Crunchy","Creamy","Smooth","Chewy","Juicy"])
    attributes.mango_consumption = random.randint(0, 50)  # Max 50

    # -----------------------------------------------------------------------
    # Belief Attributes
    # -----------------------------------------------------------------------
    # Top-level
    attributes.believes_in_god = random_choice(["Yes","No"])
    if attributes.believes_in_god == "Yes":
        attributes.religious_person_scale = random.randint(1, 10)
        attributes.religion = random_choice(["Muslim","Jew","Christian","Hindu","Buddhist","Deist"])
    else:
        attributes.religion = "Atheist"
        attributes.religious_person_scale = None
    
    # Example random fill for sub-attributes. 
    # Usually you'd check if `religion == 'Muslim'` then fill Muslim fields, else set them = None, etc.
    # For brevity, we just fill them randomly. In a real app, you'd be more selective:
    
    attributes.muslim_prays_frequency = random_choice(["Prays 5 times","Prays sometimes","Rarely","Never"])
    attributes.muslim_can_read_arabic = random_choice(["Yes","No"])
    attributes.muslim_fasts_during_ramadan = random_choice(["Always","Most of the time","Sometimes","Rarely","Never"])
    attributes.muslim_attends_friday_prayer = random_choice(["Every Friday","Occasionally","Rarely","Never"])
    attributes.muslim_eats_halal = random_choice(["Strictly Halal","Mostly Halal","Occasionally Halal","Not concerned"])
    attributes.muslim_wears_hijab = random_choice(["Always","Occasionally","Rarely","Never","Not applicable"])
    attributes.muslim_performs_zakat = random_choice(["Regularly","Occasionally","Rarely","Never"])
    attributes.muslim_reads_quran = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.muslim_participates_in_hajj = random_choice(["Has completed Hajj","Plans to complete Hajj","Does not plan to complete Hajj"])
    attributes.muslim_observes_islamic_holidays = random_choice(["Celebrates all","Celebrates some","Does not celebrate"])
    attributes.muslim_part_of_muslim_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    attributes.jew_goes_to_synagogue = random_choice(["Every Sabbath","Occasionally","Rarely","Never"])
    attributes.jew_keeps_kosher = random_choice(["Strictly Kosher","Mostly Kosher","Occasionally Kosher","Not concerned"])
    attributes.jew_observes_jewish_holidays = random_choice(["Celebrates all","Celebrates some","Does not celebrate"])
    attributes.jew_wears_kippah = random_choice(["Always","Occasionally","Rarely","Never"])
    attributes.jew_studies_torah = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.jew_part_of_jewish_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    attributes.christian_attends_church = random_choice(["Every Sunday","Occasionally","Rarely","Never"])
    attributes.christian_reads_bible = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.christian_prays = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.christian_observes_christian_holidays = random_choice(["Celebrates all","Celebrates some","Does not celebrate"])
    attributes.christian_participates_in_sacraments = random_choice(["Regularly","Occasionally","Rarely","Never"])
    attributes.christian_part_of_christian_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    attributes.hindu_prays_at_home = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.hindu_attends_temple = random_choice(["Regularly","Occasionally","Rarely","Never"])
    attributes.hindu_observes_hindu_festivals = random_choice(["Celebrates all","Celebrates some","Does not celebrate"])
    attributes.hindu_practices_vegetarianism = random_choice(["Always","Sometimes","Never"])
    attributes.hindu_studies_scriptures = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.hindu_part_of_hindu_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    attributes.buddhist_meditates = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.buddhist_attends_monastery = random_choice(["Regularly","Occasionally","Rarely","Never"])
    attributes.buddhist_observes_buddhist_holidays = random_choice(["Celebrates all","Celebrates some","Does not celebrate"])
    attributes.buddhist_practices_vegetarianism = random_choice(["Always","Sometimes","Never"])
    attributes.buddhist_studies_dharma = random_choice(["Daily","Weekly","Occasionally","Rarely","Never"])
    attributes.buddhist_part_of_buddhist_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    attributes.deist_believes_in_higher_power = random_choice(["Yes","No"])
    attributes.deist_involvement_in_organized_religion = random_choice(["Not involved","Occasionally involved","Interested but not involved"])

    attributes.atheist_identifies_as_atheist = random_choice(["Strong Atheist","Weak Atheist","Agnostic Atheist"])
    attributes.atheist_views_on_religion = random_choice(["Indifferent","Critical of Religion","Open to Spirituality"])
    attributes.atheist_engages_in_philosophical_discussions = random_choice(["Frequently","Occasionally","Rarely","Never"])
    attributes.atheist_part_of_atheist_community = random_choice(["Actively involved","Occasionally involved","Not involved"])

    # -----------------------------------------------------------------------
    # Phone Attributes
    # -----------------------------------------------------------------------
    attributes.phone_type = random_choice(["iPhoneUser","AndroidUser"])
    attributes.uses_phone_case = random_choice(["Yes","No"])

    # -----------------------------------------------------------------------
    # Job Attributes
    # -----------------------------------------------------------------------
    attributes.number_of_job_changes = random.randint(0, 10)
    attributes.years_in_current_job = random.randint(0, 20)
    attributes.total_years_of_experience = random.randint(0, 40)

    # For multi-select fields, we might store them as CSV 
    # or just pick one randomly for demonstration:
    possible_industries = ["Technology","Finance","Healthcare","Education","Retail","Manufacturing","Government","Non-profit","Other"]
    attributes.primary_industry = random_choice(possible_industries)

    attributes.current_job_title = random_choice(["Software Engineer","Project Manager","Data Analyst","Teacher","None"])
    attributes.highest_education_level = random_choice(["High School","Associate Degree","Bachelor's Degree","Master's Degree","Doctorate","Professional Certification"])

    attributes.job_satisfaction_level = random.randint(1, 10)

    # Another multi-select example; here we just pick one for simplicity
    attributes.remote_work_preference = random_choice(["Fully Remote","Hybrid","Office-based"])
    
    # Similarly for "skills":
    possible_skills = ["Project Management","Data Analysis","Software Development","Marketing","Sales","Customer Service","Financial Analysis","Human Resources","Other"]
    attributes.skills = random_choice(possible_skills)
    
    attributes.certifications = random_choice(["PMP","CPA","None","Scrum Master","AWS Certified"])
    attributes.career_goals = random_choice([
        "Become a team lead at a tech company",
        "Transition to a new industry",
        "Start a personal business",
        "None"
    ])

    # Another multi-select example (company size)
    attributes.company_size_preference = random_choice([
        "Startup (1-50 employees)",
        "Small (51-200 employees)",
        "Medium (201-500 employees)",
        "Large (501-2000 employees)",
        "Enterprise (2001+ employees)"
    ])
    attributes.willing_to_relocate = random_choice(["Yes","No"])
    attributes.preferred_work_environment = random_choice(["Fast-paced","Collaborative","Independent","Structured","Flexible"])

    # Example numeric spending 
    attributes.spending = round(random.uniform(100.0, 10000.0), 2)

    # 4. Commit changes to the database
    session.commit()
    print(f"[SUCCESS] Random attributes assigned for user_id={user_id}.")


def main():
    """Entry point for running this script standalone."""
    # Adjust DB path/URL as needed:
    engine = create_engine('sqlite:///db/data/budget_tracker.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        fill_random_user_attributes(session, user_id=1)  
        # You can change user_id=0 to an existing user_id (e.g. 1) 
        # depending on how your data is set up
    finally:
        session.close()

if __name__ == "__main__":
    main()
