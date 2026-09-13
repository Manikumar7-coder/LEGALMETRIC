# rules.py

COMMON_RULES = {
    "common_generic_name": {
        "required": True,
        "description": "Common or generic name of the commodity"
    },

    "manufacturer_name": {
        "required": True,
        "description": "Manufacturer name"
    },

    "manufacturer_address": {
        "required": True,
        "description": "Manufacturer address"
    },

    "net_quantity": {
        "required": True,
        "description": "Net quantity with appropriate unit"
    },

    "manufacturing_date": {
        "required": True,
        "description": "Month and year of manufacture/packing/import as applicable"
    },

    "mrp": {
        "required": True,
        "description": "Retail sale price / MRP"
    },

    "consumer_care": {
        "required": True,
        "description": "Consumer complaint contact details"
    },

    "country_of_origin": {
        "required": True,
        "description": "Country of origin (Legal Metrology Amendment Rules, 2017)"
    }
}

# --- FSSAI (Food Safety and Standards) labeling requirement — separate law, food only ---
FSSAI_RULES = {
    "expiry_date": {
        "required": True,
        "description": "Best before / use by / expiry date (FSSAI labeling regulations — not Legal Metrology)"
    }
}


CATEGORY_RULES = {
    "Food": {
        "Snacks": [
            "common_generic_name",
            "manufacturer_name",
            "manufacturer_address",
            "net_quantity",
            "manufacturing_date",
            "mrp",
            "consumer_care",
            "country_of_origin",
            "expiry_date",
        ],
        "Confectionery": [
            "common_generic_name",
            "manufacturer_name",
            "manufacturer_address",
            "net_quantity",
            "manufacturing_date",
            "mrp",
            "consumer_care",
            "country_of_origin",
            "expiry_date",
        ],
    },

    "Personal Care": {
        "Soap": [
            "common_generic_name",
            "manufacturer_name",
            "manufacturer_address",
            "net_quantity",
            "manufacturing_date",
            "mrp",
            
            "consumer_care",
            "country_of_origin",
        ],
    }
}