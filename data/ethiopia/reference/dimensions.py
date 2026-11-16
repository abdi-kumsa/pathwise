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

# Opening years from the World Bank industrial-park review (see calibration.yaml
# investment.park_openings). Debre Berhan added; Kombolcha and Hawassa corrected.
INDUSTRIAL_PARKS = [
    {"name": "Eastern Industrial Zone", "region": "Oromia", "opened": 2010},
    {"name": "Bole Lemi", "region": "Addis Ababa", "opened": 2014},
    {"name": "Hawassa Industrial Park", "region": "Sidama", "opened": 2016},
    {"name": "Kombolcha Industrial Park", "region": "Amhara", "opened": 2017},
    {"name": "Mekelle Industrial Park", "region": "Tigray", "opened": 2017},
    {"name": "Adama Industrial Park", "region": "Oromia", "opened": 2018},
    {"name": "Dire Dawa Industrial Park", "region": "Dire Dawa", "opened": 2018},
    {"name": "Debre Berhan Industrial Park", "region": "Amhara", "opened": 2019},
    {"name": "Jimma Industrial Park", "region": "Oromia", "opened": 2019},
    {"name": "Bahir Dar Industrial Park", "region": "Amhara", "opened": 2020},
]

SECTORS = sorted({f["sector"] for f in FIELDS} | {"Manufacturing", "Construction", "ICT", "Health", "Agriculture", "Finance", "Public administration", "Education"})


def shock_factor(region_name: str, year: int, institution: str | None = None) -> float:
    """University-operations factor (1.0 normal, 0.0 closed) from calibration.yaml.

    Institution overrides win over the region; COVID 2020 applies everywhere.
    These factors are estimates derived from dated, sourced events.
    """
    import calibration as C
    d = C.get("disruption")
    if institution and institution in d.get("institutions", {}):
        vals = d["institutions"][institution]
        if year in vals:
            return float(vals[year])
    vals = d.get("regions", {}).get(region_name, {})
    if year in vals:
        return float(vals[year])
    return float(d["covid_2020"]) if year == 2020 else 1.0


def esslce_pass_uplift(year: int) -> float:
    """Kept for compatibility; pass rates now come from calibration.yaml exam.pass_rate_pct."""
    return 0.0
