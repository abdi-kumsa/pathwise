"""Ethiopia reference dimensions for the Wave 1 simulated fact tables.

These are structural labels (real regions, real public HEIs, MoE bands), not
official statistics. Magnitudes in the fact tables are simulated.
"""

YEARS = list(range(2016, 2026))

# 12 regional states + two city administrations (DOC1 / Wave 1.1).
REGIONS = [
    {"code": "AA", "name": "Addis Ababa", "type": "city", "tigray_shock": False},
    {"code": "DD", "name": "Dire Dawa", "type": "city", "tigray_shock": False},
    {"code": "AM", "name": "Amhara", "type": "region", "tigray_shock": False},
    {"code": "OR", "name": "Oromia", "type": "region", "tigray_shock": False},
    {"code": "TG", "name": "Tigray", "type": "region", "tigray_shock": True},
    {"code": "SN", "name": "Sidama", "type": "region", "tigray_shock": False},
    {"code": "SE", "name": "South Ethiopia", "type": "region", "tigray_shock": False},
    {"code": "SW", "name": "South West Ethiopia", "type": "region", "tigray_shock": False},
    {"code": "CN", "name": "Central Ethiopia", "type": "region", "tigray_shock": False},
    {"code": "SO", "name": "Somali", "type": "region", "tigray_shock": False},
    {"code": "AF", "name": "Afar", "type": "region", "tigray_shock": False},
    {"code": "BG", "name": "Benishangul-Gumuz", "type": "region", "tigray_shock": False},
    {"code": "GM", "name": "Gambela", "type": "region", "tigray_shock": False},
    {"code": "HR", "name": "Harari", "type": "region", "tigray_shock": False},
]

# One programme per MoE field so the join backbone stays 1:1.
FIELDS = [
    {"field": "Engineering & Technology", "band": "Natural science", "stem": True,
     "program": "BSc Civil Engineering", "occupation": "Civil Engineer", "sector": "Construction"},
    {"field": "Natural & Computational Sciences", "band": "Natural science", "stem": True,
     "program": "BSc Computer Science", "occupation": "Software Developer", "sector": "ICT"},
    {"field": "Medicine & Health Sciences", "band": "Natural science", "stem": True,
     "program": "MD Medicine", "occupation": "General Practitioner", "sector": "Health"},
    {"field": "Agriculture & Life Sciences", "band": "Natural science", "stem": True,
     "program": "BSc Agriculture", "occupation": "Agronomist", "sector": "Agriculture"},
    {"field": "Business & Economics", "band": "Social science", "stem": False,
     "program": "BA Accounting", "occupation": "Accountant", "sector": "Finance"},
    {"field": "Social Sciences & Humanities", "band": "Social science", "stem": False,
     "program": "BA Sociology", "occupation": "Social Worker", "sector": "Public administration"},
    {"field": "Law", "band": "Social science", "stem": False,
     "program": "LLB Law", "occupation": "Legal Officer", "sector": "Public administration"},
    {"field": "Education", "band": "Social science", "stem": False,
     "program": "BEd Education", "occupation": "Secondary Teacher", "sector": "Education"},
]

HEIS = [
    {"name": "Addis Ababa University", "type": "public", "generation": 1, "region": "Addis Ababa", "campus": "Sidist Kilo"},
    {"name": "Addis Ababa Science and Technology University", "type": "public", "generation": 2, "region": "Addis Ababa", "campus": "Akaki"},
    {"name": "Bahir Dar University", "type": "public", "generation": 1, "region": "Amhara", "campus": "Poly"},
    {"name": "University of Gondar", "type": "public", "generation": 1, "region": "Amhara", "campus": "Maraki"},
    {"name": "Jimma University", "type": "public", "generation": 1, "region": "Oromia", "campus": "Main"},
    {"name": "Haramaya University", "type": "public", "generation": 1, "region": "Oromia", "campus": "Main"},
    {"name": "Adama Science and Technology University", "type": "public", "generation": 2, "region": "Oromia", "campus": "Main"},
    {"name": "Hawassa University", "type": "public", "generation": 1, "region": "Sidama", "campus": "Main"},
    {"name": "Mekelle University", "type": "public", "generation": 1, "region": "Tigray", "campus": "Endayesus"},
    {"name": "Aksum University", "type": "public", "generation": 2, "region": "Tigray", "campus": "Main"},
    {"name": "Arba Minch University", "type": "public", "generation": 2, "region": "South Ethiopia", "campus": "Main"},
    {"name": "Dilla University", "type": "public", "generation": 2, "region": "South Ethiopia", "campus": "Main"},
    {"name": "Wolaita Sodo University", "type": "public", "generation": 2, "region": "South Ethiopia", "campus": "Main"},
    {"name": "Jigjiga University", "type": "public", "generation": 2, "region": "Somali", "campus": "Main"},
    {"name": "Ambo University", "type": "public", "generation": 2, "region": "Oromia", "campus": "Main"},
    {"name": "Wollo University", "type": "public", "generation": 2, "region": "Amhara", "campus": "Dessie"},
    {"name": "Debre Berhan University", "type": "public", "generation": 2, "region": "Amhara", "campus": "Main"},
    {"name": "Unity University", "type": "private", "generation": 0, "region": "Addis Ababa", "campus": "Gerji"},
    {"name": "St. Mary's University", "type": "private", "generation": 0, "region": "Addis Ababa", "campus": "Mexico"},
]

INDUSTRIAL_PARKS = [
    {"name": "Hawassa Industrial Park", "region": "Sidama", "opened": 2017},
    {"name": "Bole Lemi", "region": "Addis Ababa", "opened": 2014},
    {"name": "Eastern Industrial Zone", "region": "Oromia", "opened": 2013},
    {"name": "Adama Industrial Park", "region": "Oromia", "opened": 2018},
    {"name": "Kombolcha Industrial Park", "region": "Amhara", "opened": 2019},
    {"name": "Mekelle Industrial Park", "region": "Tigray", "opened": 2017},
    {"name": "Dire Dawa Industrial Park", "region": "Dire Dawa", "opened": 2018},
    {"name": "Jimma Industrial Park", "region": "Oromia", "opened": 2020},
    {"name": "Bahir Dar Industrial Park", "region": "Amhara", "opened": 2019},
]

SECTORS = sorted({f["sector"] for f in FIELDS} | {"Manufacturing", "Construction", "ICT", "Health", "Agriculture", "Finance", "Public administration", "Education"})


def shock_factor(region_name: str, year: int) -> float:
    """Tigray 2021–2022 discontinuity — a structural break, not noise."""
    if region_name == "Tigray" and year in (2021, 2022):
        return 0.55
    if region_name == "Tigray" and year == 2023:
        return 0.78
    return 1.0


def esslce_pass_uplift(year: int) -> float:
    """2023 assessment reform as a step change in pass rates."""
    return 8.0 if year >= 2023 else 0.0
