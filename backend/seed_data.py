"""
Seed Data Script
─────────────────
Populates the database with realistic real estate listings
matching the Aurevia brand (Austin, Miami, Denver, Nashville, etc.)

Run with:
    python seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
import os

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from app.database import AsyncSessionLocal, create_tables
from app.models.property import Property


SEED_PROPERTIES = [
    # ── Austin, TX ────────────────────────────────────────────────────────────
    {
        "address": "1204 S Congress Ave, Unit 8B",
        "city": "Austin", "state": "TX", "zip_code": "78704",
        "neighborhood": "SoCo", "latitude": 30.2489, "longitude": -97.7501,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1180,
        "property_type": "apartment", "year_built": 2019,
        "description": "Modern apartment in the heart of SoCo. Walking distance to restaurants, bars, and boutiques. Strong rental demand in one of Austin's highest-yield corridors.",
        "image_url": "img_austin.png",
        "list_price": 1_245_000, "price_per_sqft": 1055.08,
        "fair_value_estimate": 1_290_000,
        "cap_rate": 0.084, "rental_yield": 0.081,
        "monthly_rent_estimate": 8_400, "five_year_appreciation": 0.38,
        "yoy_growth": 0.067, "risk_score": 22, "vacancy_rate": 0.028,
    },
    {
        "address": "3301 Manor Rd, Unit 14",
        "city": "Austin", "state": "TX", "zip_code": "78723",
        "neighborhood": "Mueller", "latitude": 30.2977, "longitude": -97.6998,
        "bedrooms": 3, "bathrooms": 2.5, "square_feet": 1850,
        "property_type": "condo", "year_built": 2021,
        "description": "Spacious corner unit in Mueller, Austin's premier master-planned community. Minutes from UT campus and tech corridors.",
        "list_price": 875_000, "price_per_sqft": 472.97,
        "fair_value_estimate": 890_000,
        "cap_rate": 0.072, "rental_yield": 0.068,
        "monthly_rent_estimate": 5_250, "five_year_appreciation": 0.31,
        "yoy_growth": 0.058, "risk_score": 28, "vacancy_rate": 0.035,
    },
    {
        "address": "7890 Burnet Rd",
        "city": "Austin", "state": "TX", "zip_code": "78757",
        "neighborhood": "North Loop", "latitude": 30.3475, "longitude": -97.7231,
        "bedrooms": 4, "bathrooms": 3.0, "square_feet": 2400,
        "property_type": "single_family", "year_built": 2018,
        "description": "Investor-grade single-family in booming North Loop. Currently rented. Strong appreciation history.",
        "list_price": 1_680_000, "price_per_sqft": 700.00,
        "fair_value_estimate": 1_720_000,
        "cap_rate": 0.076, "rental_yield": 0.073,
        "monthly_rent_estimate": 10_600, "five_year_appreciation": 0.42,
        "yoy_growth": 0.079, "risk_score": 20, "vacancy_rate": 0.018,
    },

    # ── Miami, FL ─────────────────────────────────────────────────────────────
    {
        "address": "1100 Brickell Ave, Suite 3200",
        "city": "Miami", "state": "FL", "zip_code": "33131",
        "neighborhood": "Brickell", "latitude": 25.7553, "longitude": -80.1936,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1350,
        "property_type": "condo", "year_built": 2022,
        "description": "Ultra-luxury condo in Brickell Financial District. Floor-to-ceiling windows, resort amenities, and Biscayne Bay views. Strong short-term rental upside.",
        "list_price": 2_100_000, "price_per_sqft": 1555.56,
        "fair_value_estimate": 2_050_000,
        "cap_rate": 0.065, "rental_yield": 0.062,
        "monthly_rent_estimate": 11_400, "five_year_appreciation": 0.29,
        "yoy_growth": 0.089, "risk_score": 35, "vacancy_rate": 0.042,
    },
    {
        "address": "420 NW 26th St",
        "city": "Miami", "state": "FL", "zip_code": "33127",
        "neighborhood": "Wynwood", "latitude": 25.8030, "longitude": -80.1990,
        "bedrooms": 1, "bathrooms": 1.0, "square_feet": 720,
        "property_type": "apartment", "year_built": 2020,
        "description": "Creative district studio/1BR in Miami's Wynwood arts neighborhood. High short-term rental demand, excellent walkability.",
        "list_price": 595_000, "price_per_sqft": 826.39,
        "fair_value_estimate": 620_000,
        "cap_rate": 0.091, "rental_yield": 0.088,
        "monthly_rent_estimate": 4_500, "five_year_appreciation": 0.34,
        "yoy_growth": 0.071, "risk_score": 40, "vacancy_rate": 0.055,
    },
    {
        "address": "88 SW 7th St, Unit 2104",
        "city": "Miami", "state": "FL", "zip_code": "33130",
        "neighborhood": "Downtown Miami", "latitude": 25.7659, "longitude": -80.1934,
        "bedrooms": 3, "bathrooms": 2.0, "square_feet": 1600,
        "property_type": "condo", "year_built": 2017,
        "description": "Spacious downtown condo with stunning city views. Managed building, tenant in place at $7,200/mo.",
        "list_price": 1_050_000, "price_per_sqft": 656.25,
        "fair_value_estimate": 1_080_000,
        "cap_rate": 0.082, "rental_yield": 0.079,
        "monthly_rent_estimate": 7_200, "five_year_appreciation": 0.32,
        "yoy_growth": 0.062, "risk_score": 32, "vacancy_rate": 0.038,
    },

    # ── Denver, CO ────────────────────────────────────────────────────────────
    {
        "address": "1550 N Larimer St, Unit 302",
        "city": "Denver", "state": "CO", "zip_code": "80202",
        "neighborhood": "LoDo", "latitude": 39.7569, "longitude": -105.0034,
        "bedrooms": 2, "bathrooms": 1.5, "square_feet": 1020,
        "property_type": "condo", "year_built": 2016,
        "description": "Historic warehouse conversion in LoDo. Exposed brick, 14ft ceilings, and a private patio. High rental demand from young professionals.",
        "list_price": 680_000, "price_per_sqft": 666.67,
        "fair_value_estimate": 710_000,
        "cap_rate": 0.078, "rental_yield": 0.075,
        "monthly_rent_estimate": 4_425, "five_year_appreciation": 0.27,
        "yoy_growth": 0.053, "risk_score": 26, "vacancy_rate": 0.031,
    },
    {
        "address": "4210 Morrison Rd",
        "city": "Denver", "state": "CO", "zip_code": "80219",
        "neighborhood": "Harvey Park", "latitude": 39.7018, "longitude": -105.0420,
        "bedrooms": 4, "bathrooms": 2.0, "square_feet": 1980,
        "property_type": "single_family", "year_built": 2015,
        "description": "Value-add single-family in up-and-coming Harvey Park. Currently below-market rent. Strong renovation upside.",
        "list_price": 540_000, "price_per_sqft": 272.73,
        "fair_value_estimate": 570_000,
        "cap_rate": 0.096, "rental_yield": 0.093,
        "monthly_rent_estimate": 4_320, "five_year_appreciation": 0.41,
        "yoy_growth": 0.082, "risk_score": 38, "vacancy_rate": 0.028,
    },

    # ── Nashville, TN ─────────────────────────────────────────────────────────
    {
        "address": "800 12th Ave S, Unit 15",
        "city": "Nashville", "state": "TN", "zip_code": "37203",
        "neighborhood": "The Gulch", "latitude": 36.1487, "longitude": -86.7935,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1250,
        "property_type": "condo", "year_built": 2020,
        "description": "Modern condo in Nashville's trendiest neighborhood. LEED-certified building, rooftop pool, walkable to Broadway.",
        "list_price": 750_000, "price_per_sqft": 600.00,
        "fair_value_estimate": 770_000,
        "cap_rate": 0.087, "rental_yield": 0.084,
        "monthly_rent_estimate": 5_450, "five_year_appreciation": 0.36,
        "yoy_growth": 0.074, "risk_score": 24, "vacancy_rate": 0.025,
    },
    {
        "address": "2200 Elliott Ave",
        "city": "Nashville", "state": "TN", "zip_code": "37204",
        "neighborhood": "Berry Hill", "latitude": 36.1214, "longitude": -86.7687,
        "bedrooms": 3, "bathrooms": 2.5, "square_feet": 2100,
        "property_type": "townhouse", "year_built": 2019,
        "description": "Investor-owned townhouse in Berry Hill, Nashville's creative district. Strong STR permits available.",
        "list_price": 620_000, "price_per_sqft": 295.24,
        "fair_value_estimate": 645_000,
        "cap_rate": 0.094, "rental_yield": 0.090,
        "monthly_rent_estimate": 4_855, "five_year_appreciation": 0.44,
        "yoy_growth": 0.086, "risk_score": 30, "vacancy_rate": 0.030,
    },

    # ── Seattle, WA ───────────────────────────────────────────────────────────
    {
        "address": "500 E Pike St, Unit 820",
        "city": "Seattle", "state": "WA", "zip_code": "98122",
        "neighborhood": "Capitol Hill", "latitude": 47.6135, "longitude": -122.3216,
        "bedrooms": 1, "bathrooms": 1.0, "square_feet": 850,
        "property_type": "apartment", "year_built": 2018,
        "description": "Prime Capitol Hill apartment. Near Amazon campus, light rail, and Pike/Pine corridor. Tech worker rental demand is extremely strong.",
        "list_price": 490_000, "price_per_sqft": 576.47,
        "fair_value_estimate": 505_000,
        "cap_rate": 0.069, "rental_yield": 0.066,
        "monthly_rent_estimate": 2_815, "five_year_appreciation": 0.23,
        "yoy_growth": 0.044, "risk_score": 29, "vacancy_rate": 0.021,
    },
    {
        "address": "1801 12th Ave",
        "city": "Seattle", "state": "WA", "zip_code": "98122",
        "neighborhood": "Central District", "latitude": 47.6068, "longitude": -122.3116,
        "bedrooms": 4, "bathrooms": 3.0, "square_feet": 2600,
        "property_type": "multi_family", "year_built": 2014,
        "description": "Duplex in Seattle's Central District. Two units, both rented. Combined income $9,200/mo. Significant equity upside.",
        "list_price": 1_380_000, "price_per_sqft": 530.77,
        "fair_value_estimate": 1_420_000,
        "cap_rate": 0.080, "rental_yield": 0.077,
        "monthly_rent_estimate": 9_200, "five_year_appreciation": 0.28,
        "yoy_growth": 0.049, "risk_score": 25, "vacancy_rate": 0.019,
    },

    # ── Phoenix, AZ ───────────────────────────────────────────────────────────
    {
        "address": "4501 N 24th St, Unit 108",
        "city": "Phoenix", "state": "AZ", "zip_code": "85016",
        "neighborhood": "Biltmore", "latitude": 33.5011, "longitude": -111.9947,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1400,
        "property_type": "condo", "year_built": 2017,
        "description": "Ground-floor condo in the Biltmore area with private patio. Strong STR/MTR income potential in Phoenix's fastest-growing investment corridor.",
        "list_price": 480_000, "price_per_sqft": 342.86,
        "fair_value_estimate": 495_000,
        "cap_rate": 0.101, "rental_yield": 0.097,
        "monthly_rent_estimate": 4_040, "five_year_appreciation": 0.47,
        "yoy_growth": 0.091, "risk_score": 42, "vacancy_rate": 0.061,
    },
    {
        "address": "9820 W Thomas Rd",
        "city": "Phoenix", "state": "AZ", "zip_code": "85037",
        "neighborhood": "Maryvale", "latitude": 33.4893, "longitude": -112.2026,
        "bedrooms": 3, "bathrooms": 2.0, "square_feet": 1580,
        "property_type": "single_family", "year_built": 2012,
        "description": "Value-add single-family home in growing Maryvale submarket. Below-market rent, significant upside on lease renewal.",
        "list_price": 320_000, "price_per_sqft": 202.53,
        "fair_value_estimate": 340_000,
        "cap_rate": 0.112, "rental_yield": 0.108,
        "monthly_rent_estimate": 2_990, "five_year_appreciation": 0.52,
        "yoy_growth": 0.097, "risk_score": 55, "vacancy_rate": 0.072,
    },

    # ── Charlotte, NC ─────────────────────────────────────────────────────────
    {
        "address": "315 N Tryon St, Unit 22A",
        "city": "Charlotte", "state": "NC", "zip_code": "28202",
        "neighborhood": "Uptown", "latitude": 35.2271, "longitude": -80.8431,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1150,
        "property_type": "condo", "year_built": 2020,
        "description": "Sleek Uptown Charlotte condo with panoramic skyline views. Walking distance to Bank of America Stadium and premier dining. High corporate rental demand.",
        "list_price": 595_000, "price_per_sqft": 517.39,
        "fair_value_estimate": 615_000,
        "cap_rate": 0.088, "rental_yield": 0.084,
        "monthly_rent_estimate": 4_370, "five_year_appreciation": 0.39,
        "yoy_growth": 0.073, "risk_score": 27, "vacancy_rate": 0.029,
    },
    {
        "address": "2812 Selwyn Ave",
        "city": "Charlotte", "state": "NC", "zip_code": "28209",
        "neighborhood": "Myers Park", "latitude": 35.2020, "longitude": -80.8574,
        "bedrooms": 4, "bathrooms": 3.0, "square_feet": 2800,
        "property_type": "single_family", "year_built": 2016,
        "description": "Elegant single-family in coveted Myers Park. Top-rated school district, tree-lined streets, and strong long-term rental demand from executives.",
        "list_price": 1_150_000, "price_per_sqft": 410.71,
        "fair_value_estimate": 1_190_000,
        "cap_rate": 0.073, "rental_yield": 0.069,
        "monthly_rent_estimate": 7_000, "five_year_appreciation": 0.33,
        "yoy_growth": 0.061, "risk_score": 21, "vacancy_rate": 0.022,
    },
    {
        "address": "1640 Montford Dr",
        "city": "Charlotte", "state": "NC", "zip_code": "28209",
        "neighborhood": "Montford", "latitude": 35.2094, "longitude": -80.8601,
        "bedrooms": 2, "bathrooms": 1.5, "square_feet": 980,
        "property_type": "townhouse", "year_built": 2018,
        "description": "Modern townhouse in walkable Montford. Craft-beer district, popular restaurants within steps. Excellent short-term rental metrics.",
        "list_price": 445_000, "price_per_sqft": 454.08,
        "fair_value_estimate": 460_000,
        "cap_rate": 0.095, "rental_yield": 0.091,
        "monthly_rent_estimate": 3_520, "five_year_appreciation": 0.41,
        "yoy_growth": 0.077, "risk_score": 33, "vacancy_rate": 0.037,
    },

    # ── Raleigh, NC ───────────────────────────────────────────────────────────
    {
        "address": "411 W Morgan St, Unit 510",
        "city": "Raleigh", "state": "NC", "zip_code": "27603",
        "neighborhood": "Downtown Raleigh", "latitude": 35.7784, "longitude": -78.6446,
        "bedrooms": 1, "bathrooms": 1.0, "square_feet": 780,
        "property_type": "apartment", "year_built": 2021,
        "description": "Luxury apartment steps from Raleigh's thriving Glenwood South nightlife district. Strong tech-worker demand from RTP corridor.",
        "list_price": 390_000, "price_per_sqft": 500.00,
        "fair_value_estimate": 405_000,
        "cap_rate": 0.093, "rental_yield": 0.089,
        "monthly_rent_estimate": 3_020, "five_year_appreciation": 0.43,
        "yoy_growth": 0.081, "risk_score": 26, "vacancy_rate": 0.031,
    },
    {
        "address": "5804 Falls of Neuse Rd",
        "city": "Raleigh", "state": "NC", "zip_code": "27609",
        "neighborhood": "North Hills", "latitude": 35.8368, "longitude": -78.6297,
        "bedrooms": 3, "bathrooms": 2.5, "square_feet": 2100,
        "property_type": "townhouse", "year_built": 2019,
        "description": "North Hills townhome, Raleigh's premier mixed-use destination. Walkable to restaurants, offices, and green space. Very low vacancy history.",
        "list_price": 680_000, "price_per_sqft": 323.81,
        "fair_value_estimate": 705_000,
        "cap_rate": 0.086, "rental_yield": 0.082,
        "monthly_rent_estimate": 4_880, "five_year_appreciation": 0.37,
        "yoy_growth": 0.069, "risk_score": 23, "vacancy_rate": 0.024,
    },
    {
        "address": "200 Glenwood Ave, Unit 304",
        "city": "Raleigh", "state": "NC", "zip_code": "27603",
        "neighborhood": "Glenwood South", "latitude": 35.7839, "longitude": -78.6478,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1100,
        "property_type": "condo", "year_built": 2022,
        "description": "Brand-new condo in Raleigh's most vibrant entertainment corridor. High short-term rental income potential; rooftop pool and concierge.",
        "list_price": 520_000, "price_per_sqft": 472.73,
        "fair_value_estimate": 540_000,
        "cap_rate": 0.099, "rental_yield": 0.095,
        "monthly_rent_estimate": 4_290, "five_year_appreciation": 0.46,
        "yoy_growth": 0.088, "risk_score": 30, "vacancy_rate": 0.028,
    },

    # ── Houston, TX ───────────────────────────────────────────────────────────
    {
        "address": "2929 Weslayan St, Unit 1204",
        "city": "Houston", "state": "TX", "zip_code": "77027",
        "neighborhood": "River Oaks", "latitude": 29.7361, "longitude": -95.4271,
        "bedrooms": 3, "bathrooms": 2.5, "square_feet": 2200,
        "property_type": "condo", "year_built": 2018,
        "description": "Prestigious River Oaks condo with resort-style amenities. Located in Houston's most affluent enclave; strong executive tenant demand.",
        "list_price": 1_450_000, "price_per_sqft": 659.09,
        "fair_value_estimate": 1_495_000,
        "cap_rate": 0.069, "rental_yield": 0.065,
        "monthly_rent_estimate": 8_325, "five_year_appreciation": 0.28,
        "yoy_growth": 0.052, "risk_score": 25, "vacancy_rate": 0.023,
    },
    {
        "address": "1920 Bagby St",
        "city": "Houston", "state": "TX", "zip_code": "77002",
        "neighborhood": "Midtown", "latitude": 29.7477, "longitude": -95.3822,
        "bedrooms": 1, "bathrooms": 1.0, "square_feet": 860,
        "property_type": "apartment", "year_built": 2020,
        "description": "Midtown Houston apartment in a modern mixed-use building. Light rail access, vibrant nightlife corridor. Strong short-term and mid-term rental demand.",
        "list_price": 320_000, "price_per_sqft": 372.09,
        "fair_value_estimate": 335_000,
        "cap_rate": 0.103, "rental_yield": 0.099,
        "monthly_rent_estimate": 2_745, "five_year_appreciation": 0.45,
        "yoy_growth": 0.085, "risk_score": 44, "vacancy_rate": 0.058,
    },
    {
        "address": "7600 Westheimer Rd, Unit 2B",
        "city": "Houston", "state": "TX", "zip_code": "77063",
        "neighborhood": "Westchase", "latitude": 29.7369, "longitude": -95.5007,
        "bedrooms": 2, "bathrooms": 2.0, "square_feet": 1320,
        "property_type": "apartment", "year_built": 2015,
        "description": "Spacious apartment in Westchase energy corridor. High demand from oil & gas professionals; strong lease renewal rate.",
        "list_price": 280_000, "price_per_sqft": 212.12,
        "fair_value_estimate": 295_000,
        "cap_rate": 0.108, "rental_yield": 0.104,
        "monthly_rent_estimate": 2_520, "five_year_appreciation": 0.40,
        "yoy_growth": 0.078, "risk_score": 49, "vacancy_rate": 0.065,
    },
    {
        "address": "3310 Montrose Blvd",
        "city": "Houston", "state": "TX", "zip_code": "77006",
        "neighborhood": "Montrose", "latitude": 29.7428, "longitude": -95.3969,
        "bedrooms": 4, "bathrooms": 3.0, "square_feet": 3100,
        "property_type": "multi_family", "year_built": 2013,
        "description": "Fully occupied fourplex in Houston's eclectic Montrose arts district. Combined rent $10,400/mo. Irreplaceable walkable location.",
        "list_price": 1_220_000, "price_per_sqft": 393.55,
        "fair_value_estimate": 1_265_000,
        "cap_rate": 0.102, "rental_yield": 0.098,
        "monthly_rent_estimate": 10_400, "five_year_appreciation": 0.36,
        "yoy_growth": 0.067, "risk_score": 37, "vacancy_rate": 0.033,
    },
]


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(Property).limit(1))
        if existing.scalar_one_or_none():
            print("⚠️  Database already has data — skipping seed.")
            return

        print(f"🌱 Seeding {len(SEED_PROPERTIES)} properties...")
        for i, data in enumerate(SEED_PROPERTIES, 1):
            prop = Property(**data)
            db.add(prop)
            print(f"   {i:2}. {data['address']}, {data['city']}, {data['state']}")

        await db.commit()
        print(f"\n✅ Successfully seeded {len(SEED_PROPERTIES)} properties!")
        print("🚀 Start the server:  uvicorn app.main:app --reload")
        print("📖 View the docs:     http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
