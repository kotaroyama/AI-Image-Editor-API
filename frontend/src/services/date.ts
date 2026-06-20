export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);

  const hours = date.getHours()
  const minutes = String(date.getMinutes()).padStart(2, "0");
  
  const ampm = hours >= 12 ? "PM" : "AM";
  const displayHour = hours % 12 || 12;

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  return (
    `${displayHour}:${minutes} ${ampm} ` +
    " on " +
    `${monthNames[date.getMonth()].padStart(2, "0")} ` +
    `${String(date.getDate()).padStart(2, "0")}, ` +
    `${date.getFullYear()}`
  );
}