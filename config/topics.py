from __future__ import annotations

from typing import TypeAlias

TopicDict: TypeAlias = dict[str, str | list[str]]

TOPICS: list[TopicDict] = [
    # ── LENDER STRENGTH (positive for lenders) ──────────────────────────────
    {
        "topic_name": "lender_spread_power",
        "topic_text": (
            "{company} spread widening new deal origination pricing power direct lending"
        ),
        "polarity": "positive",
        "applies_to": ["lender"],
        "short_label": "Spread power",
        "layman_description": (
            "Ability to widen spreads or command premium pricing on new originations."
        ),
        "calculation_note": "Positive input to terms_power_score.",
    },
    {
        "topic_name": "lender_fundraise_resilience",
        "topic_text": (
            "{company} successful fundraise capital raise despite market volatility private credit"
        ),
        "polarity": "positive",
        "applies_to": ["lender"],
        "short_label": "Fundraise resilience",
        "layman_description": (
            "Successful capital raises or closes despite broader market volatility."
        ),
        "calculation_note": "Positive input to terms_power_score.",
    },
    {
        "topic_name": "lender_nav_stability",
        "topic_text": (
            "{company} net asset value stable maintained portfolio quality BDC"
        ),
        "polarity": "positive",
        "applies_to": ["lender"],
        "short_label": "NAV stability",
        "layman_description": (
            "Stable net asset value and maintained portfolio quality across the loan book."
        ),
        "calculation_note": "Positive input to terms_power_score.",
    },
    {
        "topic_name": "lender_covenant_tightening",
        "topic_text": (
            "{company} covenant tightening lender protection credit agreement amendment favorable"
        ),
        "polarity": "positive",
        "applies_to": ["lender"],
        "short_label": "Covenant tightening",
        "layman_description": (
            "Tighter covenants or lender-favorable amendments in credit agreements."
        ),
        "calculation_note": "Positive input to terms_power_score.",
    },
    # ── LENDER STRESS (negative for lenders) ────────────────────────────────
    {
        "topic_name": "redemption_pressure",
        "topic_text": (
            "{company} redemption request withdrawal investor liquidity gate private credit fund"
        ),
        "polarity": "negative",
        "applies_to": ["lender"],
        "short_label": "Redemption pressure",
        "layman_description": (
            "Investor redemption requests, withdrawal queues, or liquidity gates on fund vehicles."
        ),
        "calculation_note": "Negative input; reduces terms_power_score.",
    },
    {
        "topic_name": "nav_markdown",
        "topic_text": (
            "{company} NAV markdown write-down loan impairment portfolio devaluation"
        ),
        "polarity": "negative",
        "applies_to": ["lender"],
        "short_label": "NAV markdown",
        "layman_description": (
            "Write-downs, loan impairments, or portfolio-level NAV declines."
        ),
        "calculation_note": "Negative input; reduces terms_power_score.",
    },
    {
        "topic_name": "covenant_waiver",
        "topic_text": (
            "{company} covenant waiver amendment forbearance borrower relief private credit"
        ),
        "polarity": "negative",
        "applies_to": ["lender"],
        "short_label": "Covenant waiver",
        "layman_description": (
            "Borrower-friendly waivers or forbearance that weaken lender protections."
        ),
        "calculation_note": "Negative input; reduces terms_power_score.",
    },
    {
        "topic_name": "pik_stress",
        "topic_text": (
            "{company} PIK toggle payment in kind interest deferral non-cash accrual"
        ),
        "polarity": "negative",
        "applies_to": ["lender"],
        "short_label": "PIK stress",
        "layman_description": (
            "Payment-in-kind toggles or deferred cash interest indicating borrower cash-flow strain."
        ),
        "calculation_note": "Negative input; reduces terms_power_score.",
    },
    {
        "topic_name": "lender_fee_compression",
        "topic_text": (
            "{company} management fee reduction LP pressure performance fee cut"
        ),
        "polarity": "negative",
        "applies_to": ["lender"],
        "short_label": "Fee compression",
        "layman_description": (
            "Management or performance fee pressure from LPs, compressing manager economics."
        ),
        "calculation_note": "Negative input; reduces terms_power_score.",
    },
    # ── BORROWER RESILIENCE (positive for borrowers) ─────────────────────────
    {
        "topic_name": "borrower_revenue_growth",
        "topic_text": (
            "{company} revenue growth maintained AI product launch customer retention strong"
        ),
        "polarity": "positive",
        "applies_to": ["borrower"],
        "short_label": "Revenue growth",
        "layman_description": (
            "Top-line growth, new product traction, or strong customer retention supporting debt service capacity."
        ),
        "calculation_note": "Positive input; lowers stress_score.",
    },
    {
        "topic_name": "borrower_refinancing_success",
        "topic_text": (
            "{company} debt refinanced successfully maturity extended credit facility renewed"
        ),
        "polarity": "positive",
        "applies_to": ["borrower"],
        "short_label": "Refinancing success",
        "layman_description": (
            "Completed refinancings, maturity extensions, or renewed credit facilities reducing near-term default risk."
        ),
        "calculation_note": "Positive input; lowers stress_score.",
    },
    {
        "topic_name": "borrower_margin_expansion",
        "topic_text": (
            "{company} EBITDA growth margin expansion profitability improvement operating leverage cash flow"
        ),
        "polarity": "positive",
        "applies_to": ["borrower"],
        "short_label": "Margin / EBITDA strength",
        "layman_description": (
            "EBITDA growth, margin expansion, or cash-flow improvement strengthening coverage ratios."
        ),
        "calculation_note": "Positive input; lowers stress_score.",
    },
    {
        "topic_name": "borrower_ai_adoption",
        "topic_text": (
            "{company} AI adoption product innovation artificial intelligence growth competitive advantage"
            " new capability"
        ),
        "polarity": "positive",
        "applies_to": ["borrower"],
        "short_label": "AI adoption",
        "layman_description": (
            "AI or technology adoption positioning the borrower for competitive advantage rather than disruption."
        ),
        "calculation_note": "Positive input; lowers stress_score.",
    },
    # ── BORROWER DISTRESS (negative for borrowers) ───────────────────────────
    {
        "topic_name": "ai_disruption_risk",
        "topic_text": (
            "{company} AI disruption software pricing power erosion competitive threat automation SaaS"
        ),
        "polarity": "negative",
        "applies_to": ["borrower"],
        "short_label": "AI disruption risk",
        "layman_description": (
            "Threat of AI or automation eroding the borrower's pricing power, TAM, or competitive moat."
        ),
        "calculation_note": "Negative input; raises stress_score.",
    },
    {
        "topic_name": "maturity_wall",
        "topic_text": (
            "{company} debt maturity 2026 2027 refinancing risk leveraged loan BDC private credit wall"
        ),
        "polarity": "negative",
        "applies_to": ["borrower"],
        "short_label": "Maturity wall",
        "layman_description": (
            "Concentration of upcoming debt maturities creating refinancing risk in a tight rate environment."
        ),
        "calculation_note": "Negative input; raises stress_score.",
    },
    {
        "topic_name": "default_risk",
        "topic_text": (
            "{company} default restructuring missed payment interest coverage ratio covenant breach"
        ),
        "polarity": "negative",
        "applies_to": ["borrower"],
        "short_label": "Default / restructuring",
        "layman_description": (
            "Missed payments, covenant breaches, or restructuring activity indicating credit deterioration."
        ),
        "calculation_note": "Negative input; raises stress_score.",
    },
    {
        "topic_name": "customer_churn",
        "topic_text": (
            "{company} customer churn revenue decline pricing pressure net revenue retention"
        ),
        "polarity": "negative",
        "applies_to": ["borrower"],
        "short_label": "Customer churn",
        "layman_description": (
            "Declining net revenue retention, customer losses, or pricing pressure compressing top-line."
        ),
        "calculation_note": "Negative input; raises stress_score.",
    },
    # ── BANK / BACK-LEVERAGE LAYER ───────────────────────────────────────────
    {
        "topic_name": "bank_credit_pullback",
        "topic_text": (
            "{company} back leverage restriction NAV line collateral markdown private credit bank pullback"
        ),
        "polarity": "negative",
        "applies_to": ["bank"],
        "short_label": "Credit pullback",
        "layman_description": (
            "Tightening or withdrawal of back-leverage facilities, NAV lines, or collateral terms."
        ),
        "calculation_note": "Negative input; reduces net position score.",
    },
    {
        "topic_name": "bank_margin_call",
        "topic_text": (
            "{company} margin call collateral posting leverage reduction private credit financing"
        ),
        "polarity": "negative",
        "applies_to": ["bank"],
        "short_label": "Margin call",
        "layman_description": (
            "Margin calls or forced collateral posting on private credit financing lines."
        ),
        "calculation_note": "Negative input; reduces net position score.",
    },
    {
        "topic_name": "bank_market_share_gain",
        "topic_text": (
            "{company} private credit market share gain conservative exposure winner lending"
        ),
        "polarity": "positive",
        "applies_to": ["bank"],
        "short_label": "Market share gain",
        "layman_description": (
            "Growing private credit lending share or disciplined, constructive exposure positioning."
        ),
        "calculation_note": "Positive input; raises net position score.",
    },
    {
        "topic_name": "bank_contagion_risk",
        "topic_text": (
            "{company} private credit contagion exposure loss bank risk financial stability"
        ),
        "polarity": "negative",
        "applies_to": ["bank"],
        "short_label": "Contagion risk",
        "layman_description": (
            "Exposure to private credit losses or contagion pathways that could impair the bank."
        ),
        "calculation_note": "Negative input; reduces net position score.",
    },
]
