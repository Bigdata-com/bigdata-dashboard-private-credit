from __future__ import annotations

from typing import TypeAlias

EntityDict: TypeAlias = dict[str, str | None]

# When False, banks are excluded from search/scores and hidden in HTML/Excel.
INCLUDE_BANKS_LAYER: bool = False

LENDERS: list[EntityDict] = [
    {"name": "Blackstone", "ticker": "BCRED", "layer": "lender"},
    {"name": "Ares Management", "ticker": "ASIF", "layer": "lender"},
    {"name": "Apollo Global", "ticker": "ADS", "layer": "lender"},
    {"name": "Blue Owl Capital", "ticker": "OWL", "layer": "lender"},
    {"name": "KKR", "ticker": "KKR", "layer": "lender"},
    {"name": "HPS Investment Partners", "ticker": None, "layer": "lender"},
    {"name": "UBS O'Connor", "ticker": "UBS", "layer": "lender"},
    {"name": "Brookfield Asset Management", "ticker": "BAM", "layer": "lender"},
    {"name": "Golub Capital", "ticker": "GBDC", "layer": "lender"},
    {"name": "Oaktree Capital", "ticker": "OCS", "layer": "lender"},
    {"name": "Marathon Asset Management", "ticker": None, "layer": "lender"},
    {"name": "Strategic Value Partners", "ticker": None, "layer": "lender"},
    {"name": "Marblegate Asset Management", "ticker": None, "layer": "lender"},
    {"name": "Sixth Street Partners", "ticker": "TSLX", "layer": "lender"},
    {"name": "TCW", "ticker": None, "layer": "lender"},
    {"name": "SLR Investment Corp.", "ticker": "SLRC", "layer": "lender"},
    {"name": "Fortress Investment Group", "ticker": None, "layer": "lender"},
    {"name": "Partners Group", "ticker": "PGHN", "layer": "lender"},
    {"name": "PGIM Private Credit", "ticker": "PRU", "layer": "lender"},
    {"name": "AGL Private Credit Income Fund", "ticker": None, "layer": "lender"},
]

BORROWERS: list[EntityDict] = [
    {"name": "Cision", "ticker": None, "layer": "borrower"},
    {"name": "Sitecore", "ticker": None, "layer": "borrower"},
    {"name": "Optimizely", "ticker": None, "layer": "borrower"},
    {"name": "Conductor", "ticker": None, "layer": "borrower"},
    {"name": "Allego", "ticker": None, "layer": "borrower"},
    {"name": "Seismic", "ticker": None, "layer": "borrower"},
    {"name": "Outreach", "ticker": None, "layer": "borrower"},
    {"name": "Skillsoft", "ticker": "SKIL", "layer": "borrower"},
    {"name": "Instructure", "ticker": "INST", "layer": "borrower"},
    {"name": "Cornerstone OnDemand", "ticker": None, "layer": "borrower"},
    {"name": "Integral Ad Science", "ticker": "IAS", "layer": "borrower"},
    {"name": "Conga", "ticker": None, "layer": "borrower"},
    {"name": "JAMF", "ticker": "JAMF", "layer": "borrower"},
    {"name": "Syndigo", "ticker": None, "layer": "borrower"},
    {"name": "Peraton", "ticker": None, "layer": "borrower"},
    {"name": "Medallia", "ticker": None, "layer": "borrower"},
    {"name": "First Brands", "ticker": None, "layer": "borrower"},
    {"name": "Informatica", "ticker": "INFA", "layer": "borrower"},
    {"name": "Dun & Bradstreet", "ticker": "DNB", "layer": "borrower"},
    {"name": "Solera", "ticker": None, "layer": "borrower"},
    {"name": "Epicor", "ticker": None, "layer": "borrower"},
    {"name": "Zendesk", "ticker": None, "layer": "borrower"},
    {"name": "Cotiviti", "ticker": None, "layer": "borrower"},
    {"name": "Cloudera", "ticker": None, "layer": "borrower"},
]

BANKS: list[EntityDict] = [
    {"name": "JPMorgan Chase", "ticker": "JPM", "layer": "bank"},
    {"name": "Goldman Sachs", "ticker": "GS", "layer": "bank"},
    {"name": "Morgan Stanley", "ticker": "MS", "layer": "bank"},
    {"name": "Barclays", "ticker": "BCS", "layer": "bank"},
    {"name": "Wells Fargo", "ticker": "WFC", "layer": "bank"},
]

ALL_ENTITIES: list[EntityDict] = LENDERS + BORROWERS + (BANKS if INCLUDE_BANKS_LAYER else [])
