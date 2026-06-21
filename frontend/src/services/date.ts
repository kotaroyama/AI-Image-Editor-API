export function formatTimestamp(timestamp: string): string {
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const date = new Date(`${timestamp}Z`);

  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    month: "long",
    day: "2-digit",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}