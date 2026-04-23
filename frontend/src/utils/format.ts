export function formatNumber(value: number, fractionDigits = 1) {
  return Number.isFinite(value) ? value.toFixed(fractionDigits) : "-";
}

export function formatWhole(value: number) {
  return Number.isFinite(value) ? new Intl.NumberFormat("en-US").format(Math.round(value)) : "-";
}

export function formatCurrencyish(value: number) {
  return Number.isFinite(value) ? value.toFixed(2) : "-";
}
