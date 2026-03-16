"""
Location data for Murshidabad district, West Bengal.
District is fixed; blocks and municipalities are selectable.
"""
from __future__ import annotations

from typing import List

DISTRICT_NAME = "Murshidabad"

# All 26 blocks of Murshidabad district (Census/Government data)
MURSHIDABAD_BLOCKS: List[str] = [
    "Farakka",
    "Raghunathganj I",
    "Raghunathganj II",
    "Sagardighi",
    "Samsherganj",
    "Suti I",
    "Suti II",
    "Beldanga I",
    "Beldanga II",
    "Berhampore",
    "Hariharpara",
    "Nowda",
    "Bharatpur I",
    "Bharatpur II",
    "Burwan",
    "Kandi",
    "Khargram",
    "Bhagawangola I",
    "Bhagawangola II",
    "Lalgola",
    "Murshidabad-Jiaganj",
    "Nabagram",
    "Domkal",
    "Jalangi",
    "Raninagar I",
    "Raninagar II",
]

# All 8 municipalities of Murshidabad district
MURSHIDABAD_MUNICIPALITIES: List[str] = [
    "Baharampur",
    "Beldanga",
    "Dhulian",
    "Domkal",
    "Jangipur",
    "Jiaganj-Azimganj",
    "Kandi",
    "Murshidabad",
]


def get_district_name() -> str:
    """Return the fixed district name."""
    return DISTRICT_NAME


def get_block_names() -> List[str]:
    """Return all block names for Murshidabad district."""
    return list(MURSHIDABAD_BLOCKS)


def get_municipality_names() -> List[str]:
    """Return all municipality names for Murshidabad district."""
    return list(MURSHIDABAD_MUNICIPALITIES)
