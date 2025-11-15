# Shared constants for the DENSO forecasting app.

ROLES = ["viewer", "planner", "marketing", "manager", "admin"]

# 5 Spark Plugs + 3 Inverters như seed_data.sql
DENSO_SKUS = [
    # Spark plugs
    {"code": "K20PR-U", "name": "Spark Plug K20PR-U Standard", "family": "Spark Plug", "category": "Ignition", "type": "Copper Core", "channel": "Aftermarket"},
    {"code": "SC20HR11", "name": "Spark Plug Iridium SC20HR11", "family": "Spark Plug", "category": "Ignition", "type": "Iridium", "channel": "Aftermarket"},
    {"code": "IK20", "name": "Spark Plug Iridium Power IK20", "family": "Spark Plug", "category": "Ignition", "type": "Iridium Power", "channel": "Aftermarket"},
    {"code": "IK22", "name": "Spark Plug Iridium TT IK22", "family": "Spark Plug", "category": "Ignition", "type": "Iridium TT", "channel": "Aftermarket"},
    {"code": "K16R-U", "name": "Spark Plug K16R-U Compact", "family": "Spark Plug", "category": "Ignition", "type": "Copper Core", "channel": "Aftermarket"},
    # Inverters
    {"code": "INV-HEV-G1", "name": "Inverter HEV Gen1", "family": "Inverter", "category": "Inverter", "type": "HEV Inverter", "channel": "OEM"},
    {"code": "INV-PHEV-G2", "name": "Inverter PHEV Gen2", "family": "Inverter", "category": "Inverter", "type": "PHEV Inverter", "channel": "OEM"},
    {"code": "INV-BEV-G1", "name": "Inverter BEV Platform A", "family": "Inverter", "category": "Inverter", "type": "BEV Inverter", "channel": "OEM"},
]

REGIONS = ["Vietnam", "Thailand", "Indonesia", "Philippines", "Malaysia", "Singapore"]
CHANNELS = ["Dealer", "E-commerce", "OEM"]
