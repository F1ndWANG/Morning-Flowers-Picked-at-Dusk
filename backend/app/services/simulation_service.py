def simulate_traffic(creative: dict, form: dict) -> dict:
  impressions = form["impressions"]
  clicks = round(impressions * creative["metrics"]["ctr"])
  conversions = round(clicks * creative["metrics"]["cvr"])
  spend = (creative["metrics"]["ecpm"] / 1000) * impressions
  gross_merchandise = conversions * form["price"]
  roi = gross_merchandise / spend if spend else 0

  return {
    "impressions": impressions,
    "clicks": clicks,
    "conversions": conversions,
    "spend": spend,
    "grossMerchandise": gross_merchandise,
    "roi": roi,
  }
