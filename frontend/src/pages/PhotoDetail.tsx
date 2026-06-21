import axios from "axios";
import { useEffect, useState, useRef } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert"
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"

import { api } from "../services/api";
import { triggerAutomaticDownload } from "../services/download.ts"

type Photo = {
  id: string,
  original_filename: string,
  url: string,
};

export default function PhotoDetail() {
  const { photoId } = useParams();

  const [photo, setPhoto] = useState<Photo>();
  const [jobStatus, setJobStatus] = useState("IDLE");
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
        const { status, url } = response.data;

        if (status === "COMPLETED") {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }
          setJobStatus("SUCCESS");

          await triggerAutomaticDownload(url);
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

  return (
    <div className="mx-auto max-w-7xl">
      <Helmet>
        <title>{photo?.original_filename ?? "Photo"} | AI Image Editor</title>
      </Helmet>
      <div className="mb-6">
        <Button variant="ghost" asChild>
          <Link to="/photos">
            ← Back to Photos
          </Link>
        </Button>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <Card>
          <CardContent className="p-4">
            <img 
              src={photo?.url}
              alt={photo?.original_filename} 
              className="w-full rounded-lg object-contain"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>
              Photo Details
            </CardTitle>

            <CardDescription>
              {photo?.original_filename}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
                onClick={() => handleRequestEdit("grayscale")}
              >
                {jobStatus === "SUBMITTING"? (
                  <>
                    <Spinner />
                    Submitting...
                  </>
                ) :(
                  "Grayscale"
                )}
              </Button>

              <Button
                disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
                onClick={() => handleRequestEdit("rembg")}
              >
                {jobStatus === "SUBMITTING"? (
                  <>
                    <Spinner />
                    Submitting...
                  </>
                ) :(
                  "Remove Background"
                )}
              </Button>

              <Button
                disabled={jobStatus === "SUBMITTING" || jobStatus === "PROCESSING"}
                onClick={() => handleRequestEdit("yolo")}
              >
                {jobStatus === "SUBMITTING"? (
                  <>
                    <Spinner />
                    Submitting...
                  </>
                ) :(
                  "Detect Objects"
                )}
              </Button>
            </div>

            <div className="border-t pt-4">
              <Button
                variant="destructive"
                onClick={deletePhoto}
              >
                Delete Photo
              </Button>
            </div>
            {jobStatus === "SUBMITTING" || jobStatus === "PROCESSING" && (
              <Alert>
                <Spinner />
                <AlertTitle>
                  Processing
                </AlertTitle>

                <AlertDescription>
                  Your image is being processed.
                  Download will begin automatically when finished.
                </AlertDescription>
              </Alert>
            )
            }
            {jobStatus === "ERROR" && (
              <Alert variant="destructive">
                <AlertTitle>
                  Processing Failed
                </AlertTitle>

                <AlertDescription>
                  {errorMessage}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}