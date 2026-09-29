"""Business Model Analysis for PSX Companies - Strategic View"""

BUSINESS_MODEL_DATA = {
    "FFC": {
        "company_name": "Fauji Fertilizer Company Limited",
        "sector": "Fertilizer",
        "what_it_sells": "DAP (Diammonium Phosphate), Urea, NPK fertilizers, sulfuric acid, phosphoric acid",
        "customer_segments": [
            "Farmers (domestic agricultural market)",
            "Distributors and retailers",
            "Industrial buyers (chemical processors)"
        ],
        "revenue_sources": {
            "Fertilizers (Urea, DAP, NPK)": "60-70%",
            "Sulfuric Acid": "15-20%",
            "Phosphoric Acid": "10-15%"
        },
        "business_model": "Vertically integrated producer - mines phosphate rock, produces phosphoric/sulfuric acid, manufactures fertilizers. Sells through distribution network to farmers via retailers.",
        "cost_structure": {
            "Raw materials (phosphate, potash)": "35-40%",
            "Energy and gas": "20-25%",
            "Labor and operations": "10-15%",
            "Logistics and distribution": "10-12%"
        },
        "cyclicality": "HIGH - Demand driven by agricultural seasons (Rabi/Kharif). Prices fluctuate with global commodity prices (phosphate, potash). Government subsidy/support policies create volatility.",
        "revenue_recurring": "SEASONAL - Heavy sales during planting seasons. Cash flow lumpy but predictable annually.",
        "export_exposure": "20-25% (FX risk) - Exports fertilizers to Middle East, Africa. Earns foreign exchange but exposed to PKR depreciation.",
        "import_dependency": "HIGH - Imports potash and phosphate rock. Heavily exposed to PKR depreciation and global commodity prices.",
        "regulatory_risk": "CRITICAL - Subject to government price controls, subsidy programs, export policies. Policy changes can dramatically impact margins.",
        "competitors": ["EFERT (Engro Fertilizers)", "FATIMA", "IFIC"],
        "competitive_advantages": [
            "Integrated phosphate mining (vertically integrated, lower costs)",
            "Largest market share (20%+)",
            "Strong brand recognition",
            "Established distribution network"
        ],
        "economic_moat": "STRONG - Vertically integrated with phosphate mining. High capex barriers to entry. Economies of scale. Brand loyalty among farmers.",
        "key_risks": [
            "Government price controls reducing margins",
            "Global commodity price volatility",
            "PKR depreciation (import costs spike)",
            "Potential policy shifts on fertilizer subsidies",
            "Agricultural weather dependency"
        ]
    },

    "EFERT": {
        "company_name": "Engro Fertilizers Limited",
        "sector": "Fertilizer",
        "what_it_sells": "Urea, DAP, NP, CAN fertilizers, specialty products",
        "customer_segments": [
            "Farmers (domestic market - primary)",
            "Distributors and dealers",
            "Institutional buyers"
        ],
        "revenue_sources": {
            "Urea fertilizer": "45-50%",
            "DAP/NP fertilizers": "35-40%",
            "CAN and specialty": "10-15%"
        },
        "business_model": "Manufacturer and marketer of fertilizers. Sources raw materials (urea from joint venture, phosphate rock from imports). Blends and packages products for agricultural market.",
        "cost_structure": {
            "Raw materials (urea, phosphate)": "40-45%",
            "Energy costs": "15-20%",
            "Manufacturing": "10-12%",
            "Distribution and marketing": "12-15%"
        },
        "cyclicality": "HIGH - Seasonal demand (planting seasons). Prices linked to global urea/phosphate prices.",
        "revenue_recurring": "SEASONAL - Lumpy cash flows tied to agricultural cycles.",
        "export_exposure": "10-15% - Limited exports. Primary focus domestic market.",
        "import_dependency": "HIGH - Depends on imported raw materials (urea, phosphate). Vulnerable to PKR depreciation.",
        "regulatory_risk": "HIGH - Government fertilizer policies, price controls, subsidy programs affect profitability.",
        "competitors": ["FFC", "FATIMA", "IFIC"],
        "competitive_advantages": [
            "Modern manufacturing facilities",
            "Strong distribution network",
            "Product innovation (specialty fertilizers)",
            "Brand recognition"
        ],
        "economic_moat": "MODERATE - No vertical integration (unlike FFC). Competing on efficiency and innovation. Higher operating leverage than peers.",
        "key_risks": [
            "Raw material price volatility",
            "Government price interventions",
            "FX exposure on imports",
            "Agricultural sector downturns",
            "Dependent on input material sourcing"
        ]
    },

    "FATIMA": {
        "company_name": "Fatima Fertilizer Company Limited",
        "sector": "Fertilizer",
        "what_it_sells": "Urea, DAP, CAN, NPK fertilizers, sulfuric acid",
        "customer_segments": [
            "Farmers (domestic primary)",
            "Fertilizer distributors",
            "Industrial chemical buyers"
        ],
        "revenue_sources": {
            "Fertilizers (Urea, DAP, CAN)": "70-75%",
            "Sulfuric Acid": "15-20%",
            "Other chemicals": "5-10%"
        },
        "business_model": "Integrated fertilizer producer with backward linkage to acid production. Manufactures from imported raw materials and locally sourced inputs.",
        "cost_structure": {
            "Raw materials": "40-45%",
            "Energy and utilities": "20-25%",
            "Operating expenses": "15-20%",
            "Distribution": "10-12%"
        },
        "cyclicality": "HIGH - Agricultural seasonal demand. Global commodity price linkage.",
        "revenue_recurring": "SEASONAL - Concentrated in planting seasons. Predictable but lumpy.",
        "export_exposure": "5-10% - Minimal exports, domestic-focused.",
        "import_dependency": "MODERATE-HIGH - Imports raw materials. Exposed to FX movements.",
        "regulatory_risk": "HIGH - Government fertilizer policy, pricing controls, subsidy changes affect operations.",
        "competitors": ["FFC", "EFERT", "IFIC"],
        "competitive_advantages": [
            "Integrated sulfuric acid production (cost efficiency)",
            "Competitive pricing",
            "Strong local market presence"
        ],
        "economic_moat": "MODERATE - Some integration (sulfuric acid). Competes on cost and distribution. Less diversified than FFC.",
        "key_risks": [
            "Government price controls",
            "Commodity price volatility",
            "PKR depreciation impact",
            "Limited vertical integration vs FFC",
            "Agricultural demand dependency"
        ]
    },

    "IFIC": {
        "company_name": "ICI Pakistan Limited",
        "sector": "Chemicals & Agro",
        "what_it_sells": "Soda ash, caustic soda, polyester, fertilizers, crop protection products, pharmaceuticals",
        "customer_segments": [
            "Chemical manufacturers (soda ash/caustic soda buyers)",
            "Textile industry (polyester fiber users)",
            "Farmers (crop protection, fertilizers)",
            "Healthcare sector (pharma)",
            "Detergent manufacturers"
        ],
        "revenue_sources": {
            "Soda ash and caustic soda": "35-40%",
            "Polyester": "25-30%",
            "Agro products": "15-20%",
            "Other chemicals": "10-15%"
        },
        "business_model": "Diversified chemical company. Integrated soda ash production from natural deposits. Manufacturing and marketing across multiple industries.",
        "cost_structure": {
            "Raw materials (trona for soda ash)": "25-30%",
            "Energy (critical for soda ash)": "20-25%",
            "Manufacturing": "15-20%",
            "Distribution and overhead": "15-20%"
        },
        "cyclicality": "MODERATE - Soda ash tied to textile/detergent demand (cyclical). Agro products tied to agriculture. Diversification reduces overall cyclicality.",
        "revenue_recurring": "MIXED - Soda ash recurring but cyclical. Polyester demand volatile. Agro products seasonal.",
        "export_exposure": "25-30% - Significant exports of soda ash and polyester (major FX earner).",
        "import_dependency": "LOW - Soda ash from domestic deposits. Self-sufficient on core product.",
        "regulatory_risk": "MODERATE - Environmental regulations on chemical manufacturing. Export policies on polyester.",
        "competitors": ["Soda ash: Limited (natural monopoly). Polyester: Multiple producers. Agro: FFC, EFERT, FATIMA"],
        "competitive_advantages": [
            "Natural soda ash deposits (cost advantage, supply security)",
            "Diversified product portfolio (reduces risk)",
            "Integrated manufacturing (economies of scale)",
            "Export markets (FX revenue)",
            "50+ year track record"
        ],
        "economic_moat": "STRONG - Natural soda ash deposits (defensible supply). Integrated operations. Established customer relationships across industries.",
        "key_risks": [
            "Textile industry cyclicality",
            "Energy cost inflation",
            "Export market sensitivity",
            "Chemical manufacturing regulations",
            "PKR depreciation (though export-beneficial)"
        ]
    },

    "LUCK": {
        "company_name": "Luckiest International Limited",
        "sector": "Trading/Diversified",
        "what_it_sells": "Trading operations in commodities, auto parts, and other goods. Active in import/export.",
        "customer_segments": [
            "Retailers and wholesalers",
            "Industrial buyers",
            "Import/export customers"
        ],
        "revenue_sources": {
            "Commodity trading": "40-50%",
            "Auto parts trading": "30-40%",
            "Other import/export": "10-20%"
        },
        "business_model": "Trading company - buys commodities and goods for resale. Operates import/export business. Margin-based model with working capital intensity.",
        "cost_structure": {
            "Cost of goods sold": "80-85%",
            "Operating expenses and overhead": "10-15%"
        },
        "cyclicality": "HIGH - Exposed to global commodity prices and rupee movements. Demand driven by overall economic activity.",
        "revenue_recurring": "LOW - Transaction-based. Lumpy revenue dependent on deals.",
        "export_exposure": "HIGH (40-50%) - Significant import/export operations. Heavy FX exposure.",
        "import_dependency": "HIGH - Business model is import/export. Heavily exposed to PKR depreciation.",
        "regulatory_risk": "MODERATE - Subject to customs/tariff policies, export regulations, commodity pricing controls.",
        "competitors": ["Other trading companies, direct importers, wholesalers"],
        "competitive_advantages": [
            "Established supplier relationships",
            "Trading network and logistics",
            "Working capital efficiency"
        ],
        "economic_moat": "WEAK - Trading is low-barrier business. Advantage in relationships and execution, not structural.",
        "key_risks": [
            "PKR depreciation (erodes margins on imports)",
            "Commodity price volatility (inventory risk)",
            "Working capital requirements (cash flow intensive)",
            "FX exposure on exports",
            "Low barriers to competition"
        ]
    },

    "DGKC": {
        "company_name": "Dewan Ghazi Khan Cement Company Limited",
        "sector": "Cement",
        "what_it_sells": "Portland cement, clinker",
        "customer_segments": [
            "Construction industry (retailers, contractors, builders)",
            "Ready-mix concrete producers",
            "Infrastructure projects",
            "Cement distributors"
        ],
        "revenue_sources": {
            "Cement sales": "90-95%",
            "Clinker sales": "5-10%"
        },
        "business_model": "Cement manufacturer. Quarries limestone, produces clinker, grinds into cement. Sells through distribution network to construction sector.",
        "cost_structure": {
            "Raw materials (limestone)": "20-25%",
            "Fuel and energy": "20-25%",
            "Labor": "8-10%",
            "Transport and distribution": "15-20%",
            "Operating expenses": "10-15%"
        },
        "cyclicality": "MODERATE-HIGH - Cement demand tied to construction activity (which is cyclical). Influenced by infrastructure spending, real estate cycles.",
        "revenue_recurring": "STEADY - Demand fairly consistent but seasonal (construction peaks in certain seasons).",
        "export_exposure": "5-15% - Limited exports. Primarily domestic focus.",
        "import_dependency": "LOW - Most inputs (limestone) locally sourced. Energy cost is main variable.",
        "regulatory_risk": "MODERATE - Environmental regulations on cement production. Infrastructure policies affect demand.",
        "competitors": ["CHCC", "PCCL", "MLCF", "Other major cement producers"],
        "competitive_advantages": [
            "Established distribution network",
            "Modern production facilities",
            "Brand recognition in construction sector"
        ],
        "economic_moat": "MODERATE - Cement industry has moderate barriers (capex, distribution). DGKC is mid-sized competitor.",
        "key_risks": [
            "Construction sector cyclicality",
            "Energy cost volatility",
            "Overcapacity in cement industry",
            "Infrastructure spending policy changes",
            "Transportation cost inflation"
        ]
    },

    "CHCC": {
        "company_name": "Cherat Cement Company Limited",
        "sector": "Cement",
        "what_it_sells": "Portland cement",
        "customer_segments": [
            "Construction contractors and builders",
            "Cement retailers",
            "Ready-mix concrete producers",
            "Infrastructure developers"
        ],
        "revenue_sources": {
            "Cement sales": "95%+",
            "Clinker/other": "<5%"
        },
        "business_model": "Pure-play cement manufacturer. Operates quarries for limestone, produces clinker, grinds cement. Sells through established distribution.",
        "cost_structure": {
            "Raw materials": "20-25%",
            "Energy (critical cost)": "20-25%",
            "Manufacturing": "10-15%",
            "Freight and distribution": "15-20%",
            "Overhead": "10-12%"
        },
        "cyclicality": "HIGH - Cement demand directly tied to construction cycles. Sensitive to real estate, infrastructure spending.",
        "revenue_recurring": "MODERATE - Steady demand but affected by construction seasons.",
        "export_exposure": "LOW - Primarily domestic market.",
        "import_dependency": "LOW - Inputs (limestone) locally available.",
        "regulatory_risk": "MODERATE - Environmental regulations, construction policies.",
        "competitors": ["DGKC", "PCCL", "MLCF", "Other cement manufacturers"],
        "competitive_advantages": [
            "Established market position",
            "Cost-competitive operations",
            "Strong distribution in Northern Pakistan"
        ],
        "economic_moat": "MODERATE - Capex and distribution barriers. Commodity product (limited differentiation).",
        "key_risks": [
            "Construction sector downturn",
            "Energy cost inflation (major cost driver)",
            "Industry overcapacity",
            "Price competition (margin pressure)",
            "Infrastructure spending cyclicality"
        ]
    },

    "PCCL": {
        "company_name": "Patriata Cement Company Limited",
        "sector": "Cement",
        "what_it_sells": "Portland cement",
        "customer_segments": [
            "Construction sector (builders, contractors)",
            "Cement distributors and retailers",
            "Ready-mix concrete plants",
            "Infrastructure projects"
        ],
        "revenue_sources": {
            "Cement sales": "95%+",
            "Other": "<5%"
        },
        "business_model": "Cement manufacturer with integrated quarrying. Produces from limestone deposits, grinds clinker into cement. Distributes through dealers.",
        "cost_structure": {
            "Raw materials": "20-25%",
            "Energy costs": "20-25%",
            "Production": "10-12%",
            "Distribution": "15-18%",
            "Operating overhead": "10-15%"
        },
        "cyclicality": "HIGH - Construction-linked demand (cyclical). Seasonal peaks during construction season.",
        "revenue_recurring": "MODERATE - Fairly steady but subject to construction cycles.",
        "export_exposure": "LOW - Domestic market focused.",
        "import_dependency": "LOW - Limestone sourced locally.",
        "regulatory_risk": "MODERATE - Environmental rules on quarrying and production.",
        "competitors": ["DGKC", "CHCC", "MLCF"],
        "competitive_advantages": [
            "Efficient operations",
            "Good market position",
            "Established customer base"
        ],
        "economic_moat": "MODERATE - Typical cement industry moat (capex barriers, distribution network).",
        "key_risks": [
            "Construction industry downturn",
            "Energy price inflation",
            "Overcapacity in industry",
            "Commodity pricing pressure",
            "Geographic concentration (Central Punjab)"
        ]
    },

    "PRIM": {
        "company_name": "Primark Limited",
        "sector": "Retail/Trading",
        "what_it_sells": "Retail goods, consumer products (garments, textiles, home goods)",
        "customer_segments": [
            "End consumers (retail customers)",
            "Wholesale buyers"
        ],
        "revenue_sources": {
            "Retail sales": "70-80%",
            "Wholesale/export": "20-30%"
        },
        "business_model": "Retail trading company. Sources products (textiles, garments, home goods), sells through retail stores and wholesale.",
        "cost_structure": {
            "Cost of goods": "50-60%",
            "Retail operations": "15-20%",
            "Staff and overhead": "10-15%",
            "Rent and utilities": "10-12%"
        },
        "cyclicality": "MODERATE - Consumer spending tied to economic growth, inflation, purchasing power.",
        "revenue_recurring": "STEADY - Retail revenue fairly predictable but seasonal (peak during holidays/shopping seasons).",
        "export_exposure": "10-20% - Some wholesale export to regional markets.",
        "import_dependency": "MODERATE - Sources products both locally and internationally.",
        "regulatory_risk": "MODERATE - Retail regulations, labor laws, customs duties on imports.",
        "competitors": ["Other retail chains, street retailers, online platforms"],
        "competitive_advantages": [
            "Established retail locations",
            "Brand recognition",
            "Supplier relationships"
        ],
        "economic_moat": "WEAK-MODERATE - Retail is competitive, high-traffic stores valuable. Limited structural advantages.",
        "key_risks": [
            "Consumer spending sensitivity",
            "E-commerce competition",
            "Rent and operating cost inflation",
            "Import cost increases",
            "Changing consumer preferences"
        ]
    },

    "MLCF": {
        "company_name": "Maple Leaf Cement Company Limited",
        "sector": "Cement",
        "what_it_sells": "Portland cement, cement clinker",
        "customer_segments": [
            "Construction sector (contractors, builders)",
            "Cement dealers and retailers",
            "Ready-mix concrete producers",
            "Infrastructure projects"
        ],
        "revenue_sources": {
            "Cement sales": "90-95%",
            "Clinker sales": "5-10%"
        },
        "business_model": "Cement manufacturer. Quarries raw materials, produces clinker in kilns, grinds into cement. Sells through distribution network.",
        "cost_structure": {
            "Raw materials (limestone)": "20-25%",
            "Energy (kiln operations)": "20-25%",
            "Manufacturing labor": "8-10%",
            "Distribution and logistics": "15-20%",
            "Overhead": "10-15%"
        },
        "cyclicality": "HIGH - Construction sector dependent. Strong in infrastructure booms, weak in downturns.",
        "revenue_recurring": "MODERATE - Steady demand but affected by construction cycles.",
        "export_exposure": "5-10% - Limited regional exports.",
        "import_dependency": "LOW - Raw materials locally sourced.",
        "regulatory_risk": "MODERATE - Environmental regulations on cement manufacturing.",
        "competitors": ["DGKC", "CHCC", "PCCL", "Other cement producers"],
        "competitive_advantages": [
            "Modern kiln technology",
            "Cost-efficient operations",
            "Established distribution"
        ],
        "economic_moat": "MODERATE - Cement industry has moderate barriers (capex, distribution). MLCF mid-sized player.",
        "key_risks": [
            "Construction cyclicality",
            "Energy cost inflation",
            "Industry overcapacity",
            "Margin pressure from competition",
            "Infrastructure spending uncertainty"
        ]
    }
}


def get_business_model_analysis(ticker: str) -> dict:
    """Fetch business model analysis for a company"""
    ticker = ticker.upper()
    if ticker not in BUSINESS_MODEL_DATA:
        return None

    return {
        "ticker": ticker,
        "business_model": BUSINESS_MODEL_DATA[ticker]
    }


def get_all_business_models() -> dict:
    """Get all business model data"""
    return BUSINESS_MODEL_DATA


def get_business_model_summary(ticker: str) -> str:
    """Get brief business model summary"""
    ticker = ticker.upper()
    if ticker not in BUSINESS_MODEL_DATA:
        return None

    data = BUSINESS_MODEL_DATA[ticker]
    return f"{data['company_name']}: {data['business_model']}"
