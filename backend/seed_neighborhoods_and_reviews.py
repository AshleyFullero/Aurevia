#!/usr/bin/env python3
"""
Aurevia Seed Script — Neighborhoods, Reviews & Market Price History
════════════════════════════════════════════════════════════════════
Seeds realistic data for the 3 new backend domains:
  1. Neighborhoods — 40 neighborhoods across 8 cities
  2. Reviews       — 25 investor testimonials (featured + standard)
  3. Price History — 24 months of synthetic price trends per market

Usage:
    cd backend
    python seed_neighborhoods_and_reviews.py

The script is idempotent — it clears existing data first.
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Allow imports from the app package
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal, engine
from app.models.neighborhood import Neighborhood
from app.models.price_history import PriceHistory
from app.models.review import Review
import app.models  # noqa: F401 — register all models


# ════════════════════════════════════════════════════════════════════════════════
# NEIGHBORHOOD DATA
# ════════════════════════════════════════════════════════════════════════════════

NEIGHBORHOODS: list[dict] = [
    # ── Austin, TX ──────────────────────────────────────────────────────────────
    {
        "city": "Austin", "state": "TX", "neighborhood_name": "East Austin",
        "walk_score": 78, "transit_score": 52, "bike_score": 82,
        "school_rating": 7.2, "school_count": 8, "crime_index": 38, "crime_label": "Low",
        "median_household_income": 92000, "population_density": 4800, "median_age": 31.4,
        "restaurant_count": 145, "grocery_count": 6, "park_count": 12, "gym_count": 9,
        "hospital_distance_miles": 1.8,
        "top_amenities": json.dumps(["Whisler's Bar", "Ladybird Lake Trail", "Blue Starlite Drive-In"]),
        "livability_score": 74, "popularity_trend": "rising", "gentrification_risk": "high",
    },
    {
        "city": "Austin", "state": "TX", "neighborhood_name": "South Congress (SoCo)",
        "walk_score": 85, "transit_score": 60, "bike_score": 79,
        "school_rating": 7.8, "school_count": 10, "crime_index": 32, "crime_label": "Low",
        "median_household_income": 105000, "population_density": 5200, "median_age": 33.1,
        "restaurant_count": 178, "grocery_count": 8, "park_count": 9, "gym_count": 12,
        "hospital_distance_miles": 2.1,
        "top_amenities": json.dumps(["Güero's Taco Bar", "Hotel San José", "Alamo Drafthouse"]),
        "livability_score": 81, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
    {
        "city": "Austin", "state": "TX", "neighborhood_name": "Mueller",
        "walk_score": 72, "transit_score": 45, "bike_score": 88,
        "school_rating": 8.5, "school_count": 6, "crime_index": 22, "crime_label": "Very Low",
        "median_household_income": 118000, "population_density": 3900, "median_age": 35.8,
        "restaurant_count": 62, "grocery_count": 4, "park_count": 18, "gym_count": 5,
        "hospital_distance_miles": 0.9,
        "top_amenities": json.dumps(["Mueller Lake Park", "Farmers Market", "Thinkery Museum"]),
        "livability_score": 83, "popularity_trend": "stable", "gentrification_risk": "low",
    },
    {
        "city": "Austin", "state": "TX", "neighborhood_name": "The Domain",
        "walk_score": 68, "transit_score": 42, "bike_score": 55,
        "school_rating": 8.0, "school_count": 4, "crime_index": 28, "crime_label": "Low",
        "median_household_income": 125000, "population_density": 2800, "median_age": 30.5,
        "restaurant_count": 95, "grocery_count": 5, "park_count": 5, "gym_count": 8,
        "hospital_distance_miles": 3.2,
        "top_amenities": json.dumps(["Domain Northside", "Whole Foods", "TopGolf"]),
        "livability_score": 76, "popularity_trend": "stable", "gentrification_risk": "low",
    },
    {
        "city": "Austin", "state": "TX", "neighborhood_name": "Hyde Park",
        "walk_score": 80, "transit_score": 55, "bike_score": 76,
        "school_rating": 8.3, "school_count": 7, "crime_index": 25, "crime_label": "Very Low",
        "median_household_income": 98000, "population_density": 4100, "median_age": 34.2,
        "restaurant_count": 88, "grocery_count": 5, "park_count": 8, "gym_count": 6,
        "hospital_distance_miles": 1.5,
        "top_amenities": json.dumps(["Shipe Park Pool", "Quack's Bakery", "Antonelli's Cheese Shop"]),
        "livability_score": 79, "popularity_trend": "stable", "gentrification_risk": "low",
    },

    # ── Miami, FL ───────────────────────────────────────────────────────────────
    {
        "city": "Miami", "state": "FL", "neighborhood_name": "Brickell",
        "walk_score": 91, "transit_score": 75, "bike_score": 62,
        "school_rating": 7.0, "school_count": 9, "crime_index": 42, "crime_label": "Medium",
        "median_household_income": 115000, "population_density": 12000, "median_age": 34.8,
        "restaurant_count": 310, "grocery_count": 12, "park_count": 6, "gym_count": 18,
        "hospital_distance_miles": 0.8,
        "top_amenities": json.dumps(["Brickell City Centre", "Mary Brickell Village", "Bayfront Park"]),
        "livability_score": 82, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
    {
        "city": "Miami", "state": "FL", "neighborhood_name": "Wynwood",
        "walk_score": 84, "transit_score": 58, "bike_score": 72,
        "school_rating": 6.5, "school_count": 5, "crime_index": 48, "crime_label": "Medium",
        "median_household_income": 88000, "population_density": 6800, "median_age": 30.2,
        "restaurant_count": 195, "grocery_count": 7, "park_count": 4, "gym_count": 11,
        "hospital_distance_miles": 2.3,
        "top_amenities": json.dumps(["Wynwood Walls", "Ball & Chain", "Coyo Taco"]),
        "livability_score": 73, "popularity_trend": "rising", "gentrification_risk": "high",
    },
    {
        "city": "Miami", "state": "FL", "neighborhood_name": "Coconut Grove",
        "walk_score": 76, "transit_score": 48, "bike_score": 65,
        "school_rating": 8.2, "school_count": 11, "crime_index": 30, "crime_label": "Low",
        "median_household_income": 145000, "population_density": 5200, "median_age": 38.5,
        "restaurant_count": 142, "grocery_count": 9, "park_count": 14, "gym_count": 8,
        "hospital_distance_miles": 3.1,
        "top_amenities": json.dumps(["CocoWalk", "Peacock Park", "Barnacle Historic State Park"]),
        "livability_score": 80, "popularity_trend": "stable", "gentrification_risk": "low",
    },
    {
        "city": "Miami", "state": "FL", "neighborhood_name": "Design District",
        "walk_score": 88, "transit_score": 62, "bike_score": 68,
        "school_rating": 7.4, "school_count": 6, "crime_index": 35, "crime_label": "Low",
        "median_household_income": 132000, "population_density": 7500, "median_age": 32.1,
        "restaurant_count": 165, "grocery_count": 5, "park_count": 3, "gym_count": 14,
        "hospital_distance_miles": 1.9,
        "top_amenities": json.dumps(["Miami Design District", "Faena Forum", "Margot"]),
        "livability_score": 77, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
    {
        "city": "Miami", "state": "FL", "neighborhood_name": "Little Havana",
        "walk_score": 82, "transit_score": 65, "bike_score": 70,
        "school_rating": 6.2, "school_count": 8, "crime_index": 55, "crime_label": "Medium",
        "median_household_income": 62000, "population_density": 8900, "median_age": 40.5,
        "restaurant_count": 220, "grocery_count": 11, "park_count": 7, "gym_count": 5,
        "hospital_distance_miles": 1.5,
        "top_amenities": json.dumps(["Calle Ocho", "Tower Theater", "Domino Park"]),
        "livability_score": 65, "popularity_trend": "rising", "gentrification_risk": "high",
    },

    # ── Denver, CO ──────────────────────────────────────────────────────────────
    {
        "city": "Denver", "state": "CO", "neighborhood_name": "LoDo (Lower Downtown)",
        "walk_score": 93, "transit_score": 82, "bike_score": 89,
        "school_rating": 7.6, "school_count": 7, "crime_index": 44, "crime_label": "Medium",
        "median_household_income": 105000, "population_density": 9800, "median_age": 32.8,
        "restaurant_count": 285, "grocery_count": 10, "park_count": 8, "gym_count": 15,
        "hospital_distance_miles": 1.2,
        "top_amenities": json.dumps(["Coors Field", "Union Station", "16th Street Mall"]),
        "livability_score": 85, "popularity_trend": "stable", "gentrification_risk": "medium",
    },
    {
        "city": "Denver", "state": "CO", "neighborhood_name": "RiNo (River North)",
        "walk_score": 82, "transit_score": 65, "bike_score": 86,
        "school_rating": 7.1, "school_count": 5, "crime_index": 40, "crime_label": "Low",
        "median_household_income": 98000, "population_density": 5900, "median_age": 30.5,
        "restaurant_count": 175, "grocery_count": 7, "park_count": 6, "gym_count": 10,
        "hospital_distance_miles": 2.8,
        "top_amenities": json.dumps(["Denver Central Market", "Ratio Beerworks", "Sunnyside Park"]),
        "livability_score": 79, "popularity_trend": "rising", "gentrification_risk": "high",
    },
    {
        "city": "Denver", "state": "CO", "neighborhood_name": "Cherry Creek",
        "walk_score": 78, "transit_score": 58, "bike_score": 80,
        "school_rating": 8.8, "school_count": 9, "crime_index": 22, "crime_label": "Very Low",
        "median_household_income": 158000, "population_density": 4200, "median_age": 38.2,
        "restaurant_count": 198, "grocery_count": 12, "park_count": 11, "gym_count": 16,
        "hospital_distance_miles": 1.0,
        "top_amenities": json.dumps(["Cherry Creek Shopping Center", "Cherry Creek Trail", "Tattered Cover"]),
        "livability_score": 89, "popularity_trend": "stable", "gentrification_risk": "low",
    },

    # ── Nashville, TN ───────────────────────────────────────────────────────────
    {
        "city": "Nashville", "state": "TN", "neighborhood_name": "The Gulch",
        "walk_score": 84, "transit_score": 55, "bike_score": 62,
        "school_rating": 7.5, "school_count": 5, "crime_index": 38, "crime_label": "Low",
        "median_household_income": 102000, "population_density": 8200, "median_age": 31.8,
        "restaurant_count": 165, "grocery_count": 6, "park_count": 4, "gym_count": 14,
        "hospital_distance_miles": 1.6,
        "top_amenities": json.dumps(["Nashville Farmers Market", "5 Points", "Corsair Distillery"]),
        "livability_score": 78, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
    {
        "city": "Nashville", "state": "TN", "neighborhood_name": "East Nashville",
        "walk_score": 72, "transit_score": 42, "bike_score": 70,
        "school_rating": 7.0, "school_count": 7, "crime_index": 45, "crime_label": "Medium",
        "median_household_income": 85000, "population_density": 5100, "median_age": 32.5,
        "restaurant_count": 145, "grocery_count": 8, "park_count": 10, "gym_count": 7,
        "hospital_distance_miles": 2.9,
        "top_amenities": json.dumps(["Five Points", "Shelby Park", "Mas Tacos Por Favor"]),
        "livability_score": 71, "popularity_trend": "rising", "gentrification_risk": "high",
    },
    {
        "city": "Nashville", "state": "TN", "neighborhood_name": "Germantown",
        "walk_score": 80, "transit_score": 50, "bike_score": 75,
        "school_rating": 8.0, "school_count": 4, "crime_index": 30, "crime_label": "Low",
        "median_household_income": 112000, "population_density": 4600, "median_age": 34.5,
        "restaurant_count": 110, "grocery_count": 5, "park_count": 7, "gym_count": 8,
        "hospital_distance_miles": 1.8,
        "top_amenities": json.dumps(["Germantown Café", "Nashville Farmers Market", "Bicentennial Park"]),
        "livability_score": 80, "popularity_trend": "stable", "gentrification_risk": "low",
    },

    # ── Seattle, WA ─────────────────────────────────────────────────────────────
    {
        "city": "Seattle", "state": "WA", "neighborhood_name": "Capitol Hill",
        "walk_score": 95, "transit_score": 82, "bike_score": 80,
        "school_rating": 7.8, "school_count": 10, "crime_index": 52, "crime_label": "Medium",
        "median_household_income": 118000, "population_density": 14500, "median_age": 31.5,
        "restaurant_count": 320, "grocery_count": 14, "park_count": 10, "gym_count": 16,
        "hospital_distance_miles": 0.5,
        "top_amenities": json.dumps(["Pike/Pine Corridor", "Cal Anderson Park", "Volunteer Park"]),
        "livability_score": 86, "popularity_trend": "stable", "gentrification_risk": "medium",
    },
    {
        "city": "Seattle", "state": "WA", "neighborhood_name": "South Lake Union",
        "walk_score": 88, "transit_score": 75, "bike_score": 72,
        "school_rating": 7.4, "school_count": 6, "crime_index": 36, "crime_label": "Low",
        "median_household_income": 145000, "population_density": 11200, "median_age": 30.2,
        "restaurant_count": 195, "grocery_count": 9, "park_count": 7, "gym_count": 18,
        "hospital_distance_miles": 1.1,
        "top_amenities": json.dumps(["Lake Union Park", "Museum of History & Industry", "Amazon HQ"]),
        "livability_score": 83, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
    {
        "city": "Seattle", "state": "WA", "neighborhood_name": "Fremont",
        "walk_score": 87, "transit_score": 68, "bike_score": 88,
        "school_rating": 8.2, "school_count": 8, "crime_index": 28, "crime_label": "Low",
        "median_household_income": 128000, "population_density": 8900, "median_age": 33.8,
        "restaurant_count": 165, "grocery_count": 8, "park_count": 9, "gym_count": 10,
        "hospital_distance_miles": 2.4,
        "top_amenities": json.dumps(["Fremont Sunday Market", "Fremont Troll", "Green Lake Park"]),
        "livability_score": 85, "popularity_trend": "stable", "gentrification_risk": "low",
    },

    # ── Phoenix, AZ ─────────────────────────────────────────────────────────────
    {
        "city": "Phoenix", "state": "AZ", "neighborhood_name": "Arcadia",
        "walk_score": 52, "transit_score": 28, "bike_score": 62,
        "school_rating": 8.5, "school_count": 8, "crime_index": 18, "crime_label": "Very Low",
        "median_household_income": 138000, "population_density": 3200, "median_age": 38.5,
        "restaurant_count": 125, "grocery_count": 8, "park_count": 12, "gym_count": 9,
        "hospital_distance_miles": 2.8,
        "top_amenities": json.dumps(["Arcadia Park", "Postino Wine Café", "Paradise Bakery"]),
        "livability_score": 74, "popularity_trend": "stable", "gentrification_risk": "low",
    },
    {
        "city": "Phoenix", "state": "AZ", "neighborhood_name": "Downtown Phoenix",
        "walk_score": 78, "transit_score": 62, "bike_score": 70,
        "school_rating": 6.8, "school_count": 6, "crime_index": 55, "crime_label": "Medium",
        "median_household_income": 78000, "population_density": 6500, "median_age": 30.8,
        "restaurant_count": 180, "grocery_count": 7, "park_count": 5, "gym_count": 11,
        "hospital_distance_miles": 0.7,
        "top_amenities": json.dumps(["Roosevelt Row", "Chase Field", "US Airways Center"]),
        "livability_score": 68, "popularity_trend": "rising", "gentrification_risk": "medium",
    },

    # ── New York, NY ────────────────────────────────────────────────────────────
    {
        "city": "New York", "state": "NY", "neighborhood_name": "Astoria",
        "walk_score": 94, "transit_score": 90, "bike_score": 72,
        "school_rating": 7.5, "school_count": 18, "crime_index": 32, "crime_label": "Low",
        "median_household_income": 98000, "population_density": 28000, "median_age": 33.5,
        "restaurant_count": 485, "grocery_count": 22, "park_count": 12, "gym_count": 18,
        "hospital_distance_miles": 0.9,
        "top_amenities": json.dumps(["Steinway Street", "Astoria Park", "Museum of the Moving Image"]),
        "livability_score": 87, "popularity_trend": "stable", "gentrification_risk": "medium",
    },
    {
        "city": "New York", "state": "NY", "neighborhood_name": "Long Island City",
        "walk_score": 96, "transit_score": 92, "bike_score": 75,
        "school_rating": 7.8, "school_count": 12, "crime_index": 28, "crime_label": "Low",
        "median_household_income": 115000, "population_density": 22000, "median_age": 31.8,
        "restaurant_count": 320, "grocery_count": 15, "park_count": 8, "gym_count": 22,
        "hospital_distance_miles": 1.4,
        "top_amenities": json.dumps(["Gantry Plaza State Park", "MoMA PS1", "East River Waterfront"]),
        "livability_score": 89, "popularity_trend": "rising", "gentrification_risk": "high",
    },
    {
        "city": "New York", "state": "NY", "neighborhood_name": "Williamsburg",
        "walk_score": 97, "transit_score": 88, "bike_score": 82,
        "school_rating": 7.2, "school_count": 14, "crime_index": 35, "crime_label": "Low",
        "median_household_income": 128000, "population_density": 24500, "median_age": 31.2,
        "restaurant_count": 520, "grocery_count": 18, "park_count": 9, "gym_count": 24,
        "hospital_distance_miles": 1.2,
        "top_amenities": json.dumps(["Brooklyn Brewery", "Smorgasburg", "Domino Park"]),
        "livability_score": 88, "popularity_trend": "stable", "gentrification_risk": "medium",
    },

    # ── Chicago, IL ─────────────────────────────────────────────────────────────
    {
        "city": "Chicago", "state": "IL", "neighborhood_name": "Lincoln Park",
        "walk_score": 90, "transit_score": 80, "bike_score": 84,
        "school_rating": 8.4, "school_count": 14, "crime_index": 25, "crime_label": "Very Low",
        "median_household_income": 135000, "population_density": 18000, "median_age": 34.5,
        "restaurant_count": 380, "grocery_count": 15, "park_count": 18, "gym_count": 20,
        "hospital_distance_miles": 0.8,
        "top_amenities": json.dumps(["Lincoln Park Zoo", "North Avenue Beach", "DePaul University"]),
        "livability_score": 91, "popularity_trend": "stable", "gentrification_risk": "low",
    },
    {
        "city": "Chicago", "state": "IL", "neighborhood_name": "West Loop",
        "walk_score": 92, "transit_score": 82, "bike_score": 82,
        "school_rating": 7.8, "school_count": 8, "crime_index": 33, "crime_label": "Low",
        "median_household_income": 148000, "population_density": 14500, "median_age": 33.2,
        "restaurant_count": 280, "grocery_count": 12, "park_count": 7, "gym_count": 16,
        "hospital_distance_miles": 0.6,
        "top_amenities": json.dumps(["Restaurant Row (Randolph St)", "Fulton Market", "Mary Bartelme Park"]),
        "livability_score": 88, "popularity_trend": "rising", "gentrification_risk": "medium",
    },
]


# ════════════════════════════════════════════════════════════════════════════════
# REVIEW DATA
# ════════════════════════════════════════════════════════════════════════════════

REVIEWS: list[dict] = [
    {
        "reviewer_name": "James Kowalski",
        "reviewer_title": "Senior Portfolio Manager",
        "reviewer_company": "Apex Capital Partners",
        "avatar_initials": "JK", "avatar_color": "#4F46E5",
        "location": "Austin, TX",
        "rating": 5,
        "headline": "Found a 9.2% cap rate deal in under 48 hours",
        "body": (
            "I've been using every major RE analytics platform for 12 years, and Aurevia "
            "is the first one that felt like it was built by investors, for investors. "
            "The AI match scoring actually understands what a 9% cap rate means in context "
            "of market risk. I closed on a multi-family in East Austin inside of 2 months "
            "of joining. The time I saved on due diligence alone paid for the subscription."
        ),
        "highlight_metric": "9.2% cap rate",
        "highlight_label": "Deal Found",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 148,
    },
    {
        "reviewer_name": "Maria Liu",
        "reviewer_title": "Real Estate Investment Advisor",
        "reviewer_company": "Blackstone RE Group",
        "avatar_initials": "ML", "avatar_color": "#0EA5E9",
        "location": "Miami, FL",
        "rating": 5,
        "headline": "The neighborhood intelligence is a genuine market advantage",
        "body": (
            "What sets Aurevia apart is depth of data — I'm talking walk scores, school "
            "ratings, crime indices, and vacancy trends all in one view alongside cap rates. "
            "I used it to shortlist 3 Brickell condos and identify that one had a micro-market "
            "vacancy risk that wasn't obvious from the listing. Saved me from a bad position."
        ),
        "highlight_metric": "62% faster research",
        "highlight_label": "Time Saved",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 112,
    },
    {
        "reviewer_name": "Sarah Rahman",
        "reviewer_title": "Angel Investor & LP",
        "reviewer_company": "Westbridge Ventures",
        "avatar_initials": "SR", "avatar_color": "#10B981",
        "location": "Seattle, WA",
        "rating": 5,
        "headline": "Finally — real estate analysis that doesn't require a PhD",
        "body": (
            "I was always intimidated by cap rates and IRR calculations. Aurevia explains "
            "every metric with context ('8.4% is above the Seattle market average of 6.1%'). "
            "The compare tool is incredibly powerful — side-by-side winners for every metric "
            "across 4 properties made my decision crystal clear. I'm now running a $2.4M "
            "portfolio I built entirely with Aurevia insights."
        ),
        "highlight_metric": "$2.4M portfolio",
        "highlight_label": "Portfolio Built",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 97,
    },
    {
        "reviewer_name": "David Chen",
        "reviewer_title": "Chief Investment Officer",
        "reviewer_company": "Pacific Rim Properties",
        "avatar_initials": "DC", "avatar_color": "#F59E0B",
        "location": "San Francisco, CA",
        "rating": 5,
        "headline": "The AI match score is eerily accurate",
        "body": (
            "I submitted my investment criteria — 8.5%+ cap rate, 2-3 bedrooms, low risk, "
            "West Coast markets — and the top-ranked result was a property I had independently "
            "already flagged from my own research. The algorithm clearly goes beyond simple "
            "filter matching. The NOI and cash-on-cash calculations are solid, institutional-grade."
        ),
        "highlight_metric": "94% match accuracy",
        "highlight_label": "AI Accuracy",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 134,
    },
    {
        "reviewer_name": "Michael Torres",
        "reviewer_title": "Independent Investor",
        "avatar_initials": "MT", "avatar_color": "#8B5CF6",
        "location": "Denver, CO",
        "rating": 5,
        "headline": "Replaced 3 separate tools I was paying for",
        "body": (
            "I was previously paying for a separate market data tool, a financial modeling "
            "spreadsheet service, and a property database. Aurevia does all of it, better, "
            "with a much cleaner UI. The market price history charts are beautiful, and the "
            "6-month forecast gave me the confidence to enter the Denver market at the right time."
        ),
        "highlight_metric": "3 tools replaced",
        "highlight_label": "Tools Consolidated",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 88,
    },
    {
        "reviewer_name": "Amanda Foster",
        "reviewer_title": "Property Developer",
        "reviewer_company": "Cornerstone Development",
        "avatar_initials": "AF", "avatar_color": "#EC4899",
        "location": "Nashville, TN",
        "rating": 5,
        "headline": "The compare tool alone is worth the subscription",
        "body": (
            "Running a 4-way comparison with cap rate winners, risk score leaders, "
            "and appreciation potential highlighted in one clean view — this is what "
            "institutional-grade tools should look like. I've used it with 11 clients "
            "this quarter alone to help them make better decisions faster."
        ),
        "highlight_metric": "11 client deals",
        "highlight_label": "Deals Closed",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 76,
    },
    {
        "reviewer_name": "Robert Osei",
        "reviewer_title": "Family Office Manager",
        "avatar_initials": "RO", "avatar_color": "#14B8A6",
        "location": "New York, NY",
        "rating": 5,
        "headline": "Institutional-grade analytics, finally democratized",
        "body": (
            "The type of market intelligence Aurevia provides was previously only accessible "
            "to large institutions with proprietary data teams. The market heatmap feature "
            "let me identify Nashville as an emerging high-yield market 6 months before "
            "my traditional research would have flagged it. That insight alone was worth $300K."
        ),
        "highlight_metric": "$300K insight",
        "highlight_label": "Value Identified",
        "is_featured": True, "source": "platform", "verified": True, "helpful_count": 155,
    },
    # Standard reviews (not featured)
    {
        "reviewer_name": "Lisa Park",
        "reviewer_title": "First-time Investor",
        "avatar_initials": "LP", "avatar_color": "#6366F1",
        "location": "Phoenix, AZ",
        "rating": 5,
        "headline": "Made my first investment decision with confidence",
        "body": (
            "As a first-time real estate investor, I was terrified of making the wrong choice. "
            "Aurevia's risk scores and plain-English explanations gave me the confidence to "
            "pull the trigger on a Phoenix townhouse. Six months later, rental yield is "
            "tracking exactly at the 7.8% estimate."
        ),
        "highlight_metric": "7.8% yield",
        "highlight_label": "Tracked Exactly",
        "is_featured": False, "source": "platform", "verified": True, "helpful_count": 42,
    },
    {
        "reviewer_name": "Kevin Walsh",
        "reviewer_title": "Real Estate Broker",
        "reviewer_company": "Compass",
        "avatar_initials": "KW", "avatar_color": "#0F766E",
        "location": "Chicago, IL",
        "rating": 5,
        "headline": "I recommend this to every investor client",
        "body": (
            "As a broker, I've started using Aurevia in every client conversation. "
            "Being able to pull up the full investment analytics for a property — NOI, "
            "cash-on-cash, IRR estimate — in real time during a showing has completely "
            "changed how I work. Clients trust me more because I come with data."
        ),
        "is_featured": False, "source": "platform", "verified": True, "helpful_count": 65,
    },
    {
        "reviewer_name": "Priya Nair",
        "reviewer_title": "Portfolio Analyst",
        "reviewer_company": "Meridian Capital",
        "avatar_initials": "PN", "avatar_color": "#BE185D",
        "location": "Austin, TX",
        "rating": 4,
        "headline": "Excellent platform with one minor limitation",
        "body": (
            "The analytics are genuinely best-in-class. My only wish is for more markets "
            "outside the major metro areas. That said, for the markets covered, the depth "
            "is unmatched. The natural language search is surprisingly effective — I typed "
            "'low risk condo under $800K in Miami' and it returned exactly what I needed."
        ),
        "is_featured": False, "source": "platform", "verified": True, "helpful_count": 38,
    },
    {
        "reviewer_name": "Tom Bradley",
        "reviewer_title": "Retired Investor",
        "avatar_initials": "TB", "avatar_color": "#B45309",
        "location": "Denver, CO",
        "rating": 5,
        "headline": "Clear, trustworthy, and beautifully designed",
        "body": (
            "I'm 61 years old and not particularly tech-savvy, but I found Aurevia "
            "completely intuitive. The market history charts are clear, the metrics have "
            "context, and I never feel lost. I've built a retirement-ready portfolio of "
            "4 properties using this platform over the past 18 months."
        ),
        "highlight_metric": "4 properties",
        "highlight_label": "Portfolio",
        "is_featured": False, "source": "platform", "verified": False, "helpful_count": 22,
    },
    {
        "reviewer_name": "Olivia Barnes",
        "reviewer_title": "High-Net-Worth Investor",
        "avatar_initials": "OB", "avatar_color": "#7C3AED",
        "location": "Seattle, WA",
        "rating": 5,
        "headline": "The portfolio tracker is a game changer",
        "body": (
            "Being able to see my whole portfolio in one place — total equity, monthly income, "
            "weighted cap rate, cash flow — is something I couldn't do before without a complex "
            "spreadsheet. The mortgage calculator is accurate too. Exactly the tool I needed."
        ),
        "highlight_metric": "$14,200/mo income",
        "highlight_label": "Monthly Cash Flow",
        "is_featured": False, "source": "platform", "verified": True, "helpful_count": 58,
    },
    {
        "reviewer_name": "Carlos Mendez",
        "reviewer_title": "Real Estate Syndicator",
        "avatar_initials": "CM", "avatar_color": "#047857",
        "location": "Miami, FL",
        "rating": 4,
        "headline": "Very strong for syndication deal sourcing",
        "body": (
            "The trending and natural language search make deal sourcing much faster. "
            "I run 6 syndications a year and Aurevia has been part of 3 of them in the "
            "last 12 months. The AI match score helps me quickly identify properties "
            "that fit the return profile I need for investor presentations."
        ),
        "is_featured": False, "source": "platform", "verified": True, "helpful_count": 31,
    },
    {
        "reviewer_name": "Emma Wilson",
        "reviewer_title": "Property Manager",
        "reviewer_company": "Keystone Properties",
        "avatar_initials": "EW", "avatar_color": "#1D4ED8",
        "location": "Nashville, TN",
        "rating": 5,
        "headline": "The best real estate SaaS I've ever used",
        "body": (
            "Hands down. The UI is polished, the data is reliable, and the team clearly "
            "understands the investment mindset. The favourites and compare features "
            "streamline client demos enormously. I've converted 3 clients who were "
            "previously using competitor platforms."
        ),
        "is_featured": False, "source": "google", "verified": False, "helpful_count": 44,
    },
]


# ════════════════════════════════════════════════════════════════════════════════
# MARKET PRICE HISTORY GENERATION
# ════════════════════════════════════════════════════════════════════════════════

def _generate_price_history() -> list[dict]:
    """
    Generate 24 months of synthetic monthly price history for each major market.
    Uses a realistic baseline with slight upward trend + noise.
    """
    markets = [
        # (city, state, base_price, cap_rate_base, yield_base, growth_rate)
        ("Austin",    "TX", 680000, 0.082, 0.071, 0.005),
        ("Miami",     "FL", 720000, 0.088, 0.079, 0.006),
        ("Denver",    "CO", 620000, 0.076, 0.068, 0.004),
        ("Nashville", "TN", 520000, 0.091, 0.082, 0.007),
        ("Seattle",   "WA", 780000, 0.072, 0.065, 0.004),
        ("Phoenix",   "AZ", 480000, 0.086, 0.078, 0.006),
        ("New York",  "NY", 1100000, 0.062, 0.058, 0.003),
        ("Chicago",   "IL", 520000, 0.085, 0.077, 0.004),
    ]

    property_types = ["all", "apartment", "condo", "single_family"]

    records = []
    base_date = datetime(2023, 1, 1)

    for city, state, base_price, cap_base, yield_base, monthly_growth in markets:
        for ptype in property_types:
            # Different property types have price multipliers
            type_multiplier = {
                "all": 1.0,
                "apartment": 0.75,
                "condo": 0.85,
                "single_family": 1.25,
            }[ptype]

            price = base_price * type_multiplier
            prev_price = None

            for i in range(24):
                period_date = base_date + timedelta(days=30 * i)
                period_str = period_date.strftime("%Y-%m")

                # Add realistic noise + growth trend
                noise = random.gauss(0, 0.008)  # 0.8% std noise
                seasonal = 0.01 * abs(((i % 12) - 6) / 6)  # slight seasonal bump mid-year
                price = price * (1 + monthly_growth + noise + seasonal * 0.003)
                price = max(price * 0.85, price)  # floor at 85% to avoid extreme drops

                mom = ((price - prev_price) / prev_price) if prev_price else None
                yoy = None  # Not calculated for first 12 months in seed

                # Investment metric variation
                cap_rate = cap_base + random.gauss(0, 0.003)
                rental_yield = yield_base + random.gauss(0, 0.002)
                vacancy = random.uniform(0.04, 0.09)

                records.append({
                    "city": city,
                    "state": state,
                    "property_type": ptype,
                    "period": period_str,
                    "avg_price": round(price),
                    "median_price": round(price * 0.95),
                    "min_price": round(price * 0.65),
                    "max_price": round(price * 1.45),
                    "price_per_sqft": round(price / 1200 * type_multiplier, 1),
                    "transaction_count": random.randint(12, 85),
                    "days_on_market_avg": round(random.uniform(12, 45), 1),
                    "avg_cap_rate": round(max(0.04, min(0.15, cap_rate)), 4),
                    "avg_rental_yield": round(max(0.04, min(0.14, rental_yield)), 4),
                    "avg_vacancy_rate": round(vacancy, 4),
                    "mom_price_change": round(mom, 4) if mom else None,
                    "yoy_price_change": yoy,
                })

                prev_price = price

    return records


# ════════════════════════════════════════════════════════════════════════════════
# SEEDING LOGIC
# ════════════════════════════════════════════════════════════════════════════════

async def seed():
    """Drop & reseed neighborhoods, reviews, and price_history tables."""
    import sys, io
    # Reconfigure stdout to UTF-8 so emoji prints work on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    async with AsyncSessionLocal() as db:
        print("[*] Clearing existing seed data...")
        await db.execute(text("DELETE FROM price_history"))
        await db.execute(text("DELETE FROM reviews"))
        await db.execute(text("DELETE FROM neighborhoods"))
        await db.commit()

        # -- Neighborhoods -------------------------------------------------------
        print(f"[+] Seeding {len(NEIGHBORHOODS)} neighborhoods...")
        for data in NEIGHBORHOODS:
            n = Neighborhood(**data)
            db.add(n)
        await db.commit()
        print("    OK: Neighborhoods done.")

        # -- Reviews -------------------------------------------------------------
        print(f"[+] Seeding {len(REVIEWS)} reviews...")
        for data in REVIEWS:
            r = Review(**data)
            db.add(r)
        await db.commit()
        print("    OK: Reviews done.")

        # -- Price History -------------------------------------------------------
        records = _generate_price_history()
        print(f"[+] Seeding {len(records)} price history records...")
        for data in records:
            ph = PriceHistory(**data)
            db.add(ph)
        await db.commit()
        print("    OK: Price history done.")

        print("\n=== Seed complete! ===")
        print(f"  * {len(NEIGHBORHOODS)} neighborhoods across 8 cities")
        print(f"  * {len(REVIEWS)} investor reviews ({sum(1 for r in REVIEWS if r['is_featured'])} featured)")
        print(f"  * {len(records)} monthly price history records (24 months x 8 cities x 4 types)")


if __name__ == "__main__":
    asyncio.run(seed())
