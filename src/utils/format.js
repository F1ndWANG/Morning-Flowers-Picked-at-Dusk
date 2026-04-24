import { OBJECTIVE_LABELS, PLATFORM_LABELS, STRATEGY_LABELS } from "../config/catalog.js";

export function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
}

export function formatLift(top, base) {
  if (!base) {
    return "+0.0%";
  }
  const lift = ((top - base) / base) * 100;
  return `${lift >= 0 ? "+" : ""}${lift.toFixed(1)}%`;
}

export function formatInteger(value) {
  return Number(value).toLocaleString("zh-CN");
}

export function objectiveText(key) {
  return OBJECTIVE_LABELS[key] ?? key;
}

export function platformText(key) {
  return PLATFORM_LABELS[key] ?? key;
}

export function strategyText(key) {
  return STRATEGY_LABELS[key] ?? key;
}
