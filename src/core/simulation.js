export function simulateTraffic(creative, form) {
  const impressions = form.impressions;
  const clicks = Math.round(impressions * creative.metrics.ctr);
  const conversions = Math.round(clicks * creative.metrics.cvr);
  const spend = (creative.metrics.ecpm / 1000) * impressions;
  const grossMerchandise = conversions * form.price;
  const roi = spend ? grossMerchandise / spend : 0;

  return {
    impressions,
    clicks,
    conversions,
    spend,
    grossMerchandise,
    roi
  };
}
