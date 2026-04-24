from backend.app.services.data_service import load_catalog_data


_CATALOG = load_catalog_data()

CATEGORY_CONFIG = _CATALOG["categories"]
TONE_CONFIG = _CATALOG["tones"]
OBJECTIVE_LABELS = _CATALOG["objectives"]
PLATFORM_LABELS = _CATALOG["platforms"]
STRATEGY_LABELS = _CATALOG["strategies"]
STRATEGY_ORDER = _CATALOG["strategyOrder"]
