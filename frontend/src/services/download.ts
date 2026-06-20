export async function triggerAutomaticDownload(
    presignedUrl: string,
    action: string,
    original_filename: string,
) {
  try {
    const response = await fetch(presignedUrl);
    const rawBlob = await response.blob();

    const imageBlob = new Blob([rawBlob], { type: "image/png" });

    const blobUrl = window.URL.createObjectURL(imageBlob);

    const link = document.createElement("a");
    link.href = blobUrl;

    const fileName = original_filename.substring(0, original_filename.lastIndexOf("."))
    const fileExtention = imageBlob.type.split("/")[1];
    link.download = `edited_${action}_${fileName}.${fileExtention}`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    console.error("Auto-download failed: ", error);
  }
  }