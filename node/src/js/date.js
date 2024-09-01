export function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

export function subtractMonths(date, months) {
  const newDate = new Date(date);
  newDate.setMonth(date.getMonth() - months);
  return newDate;
}
