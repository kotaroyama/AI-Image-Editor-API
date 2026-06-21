import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"

import { toast } from "sonner";

import { api } from "../services/api";

type Photo = {
  id: string,
  original_filename: string,
  url: string,
};

export default function Dashboard() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    if (!file) return;

    setSubmitting(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      await api.post("/me/photos/upload", formData);

      toast.success("Photo uploaded successfully");

      // Clear the file input in the upload form
      const fileInput = document.getElementById("image-input") as HTMLInputElement;
      fileInput.value = "";
      
      setSubmitting(false);

      loadPhotos();
    } catch (error) {
      setSubmitting(false);
      toast.error("Photo upload failed")
    }
  }

  async function loadPhotos() {
    const response = await api.get("/me/photos");
    const data = response.data;
    setPhotos(data);
  }

  async function deletePhoto(photoId: string) {
    await api.delete(`/me/photos/${photoId}`);
    toast.success("Photo deleted successfully");
    await loadPhotos();
  }

  useEffect(() => {
    loadPhotos();
  }, []);

  return (
    <div>
      <Helmet>
        <title>Dashboard | AI Image Editor</title>
      </Helmet>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Upload Photo</CardTitle>
        <CardDescription>
          Upload an image to edit with AI tools
        </CardDescription>
        </CardHeader>

        <CardContent>
          <form 
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <Field>
              <FieldLabel htmlFor="image-input">Image</FieldLabel>
              <Input
                id="image-input"
                type="file"
                accept="image/*" 
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setFile(e.target.files[0]);
                  }
                }}
              />

              <FieldDescription>Choose an image to upload</FieldDescription>
            </Field>

            {file && (
              <p className="text-sm text-muted-foreground">
                Selected: {file.name}
              </p>
            )}

            <Button
              type="submit"
              disabled={!file || submitting}
            >
              Upload
            </Button>
            {submitting && (
              <Spinner />
            )}
          </form>
        </CardContent>
      </Card>

      <div className="mb-6 flex item-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Uploaded Photos
          </h2>
        </div>

        <p className="text-sm text-muted-foreground">
          {photos.length} photo{photos.length !== 1 ? "s": ""}
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        {photos.toReversed().map((photo: Photo) => (
          <Card
            key={photo.id}
            className="overflow-hidden"
          >
            <img
              src={ photo.url }
              alt={ photo.original_filename }
              className="aspect-square w-full object-cover"
            />

            <CardHeader>
              <CardTitle className="truncate">
                { photo.original_filename }
              </CardTitle>
            </CardHeader>

            <CardFooter className="gap-2">
              <Button asChild>
                <Link
                to={`/photos/${photo.id}`}
                >
                  Edit Image
                </Link>
              </Button>
              <Button
                variant="destructive"
                onClick={() => deletePhoto(photo.id)}
              >
                Delete
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}