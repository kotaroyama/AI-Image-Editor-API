export async function triggerAutomaticDownload(
    presignedUrl: string,
) {
  try {
    const link = document.createElement("a");
    link.href = presignedUrl;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Auto-download failed: ", error);
  }
}