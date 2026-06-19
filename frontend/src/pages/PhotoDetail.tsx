import axios from "axios";
import { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";

type Photo = {
  id: string,
  original_filename: string,
  url: string,
};

export default function PhotoDetail() {
  const { photoId } = useParams();

  const [photo, setPhoto] = useState<Photo>();
  const [jobStatus, setJobStatus] = useState("IDLE");
  const [jobUrl, setJobUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const pollingIntervalRef = useRef<number | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    loadPhoto();
  }, [photoId])

  async function loadPhoto() {
    const response = await api.get(`/me/photos/${photoId}`);
    const data = response.data;
    setPhoto(data);
  }

  async function deletePhoto() {
    alert("Do you really want to delete this photo?");
    await api.delete(`/me/photos/${photoId}`);
    navigate("/photos")
  }

  async function handleRequestEdit(action: string) {
    setJobStatus("SUBMITTING");
    setErrorMessage("");

    const fileExt = photo?.original_filename.split(".").pop();

    try {
      const response = await api.post("/me/photos/edit", {
        image_id: photoId,
        action: action,
        file_extension: fileExt,
      });

      const { job_id } = response.data;

      if (job_id) {
        setJobStatus("PROCESSING");
        startPolling(job_id);
      } else {
        throw new Error("No job ID was returned from the API.");
      }
    } catch (error) {
      setJobStatus("ERROR");

      if (axios.isAxiosError(error)){
        setErrorMessage(error.response?.data?.detail );
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Unknown error occurred.");
      }
    }
  }

  async function startPolling(jobId: string) {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await api.get(`/me/jobs/${jobId}`);
        const { original_filename, action, status, url } = response.data;

        if (status === "COMPLETED") {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }
          setJobUrl(url);
          setJobStatus("SUCCESS");

          await triggerAutomaticDownload(url, action, original_filename);
        } else if (status === "FAILED") {
          setJobStatus("ERROR");
          setErrorMessage("The processing worker encountered an error");
        }
      } catch (error) {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
        }
        console.error("Polling error: ", error);
      }
    }, 1500);
  }

  async function triggerAutomaticDownload(
    presignedUrl: string,
    action: string,
    original_filename: string,
  ) {
    try {
      const response = await fetch(presignedUrl);
      const blob = await response.blob();

      const blobUrl = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = blobUrl;

      const fileName = original_filename.substring(0, original_filename.lastIndexOf("."))
      const fileExtention = blob.type.split("/")[1];
      link.download = `edited_${action}_${fileName}.${fileExtention}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Auto-download failed: ", error);
    }
  }

  return (
    <div>
      <div>
        <div>
          <img
            src={ photo?.url }
            alt=""
            width="600"
          />
          <p>{ photo?.original_filename }</p>
          <button onClick={() => deletePhoto()}>
            Delete
          </button>
        </div>
        <Link
          to={"/photos"}
        >
          Back
        </Link>
      </div>
      <div>
        <div>
          <button
            disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
            onClick={() => handleRequestEdit("grayscale")}
          >
            {jobStatus === "SUBMITTING" ? "Conecting..." : "Grayscale"}
          </button>
          <button
            disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
            onClick={() => handleRequestEdit("rembg")}
          >
            {jobStatus === "SUBMITTING" ? "Conecting..." : "Remove Background"}
          </button>
          <button
            disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
            onClick={() => handleRequestEdit("yolo")}
          >
            {jobStatus === "SUBMITTING" ? "Conecting..." : "Detect Objects"}
          </button>
        </div>
      </div>
      {jobStatus === "SUBMITTING" || jobStatus === "PROCESSING" && (
        <p>Processing... It may take a while...</p>
      )
      }
      {jobStatus === "Error" && (
        <div>
          {errorMessage}
        </div>
      )}
    </div>
  )
}