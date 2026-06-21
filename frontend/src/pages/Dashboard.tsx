import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
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

import { api } from "../services/api";

type Photo = {
  id: string,
  original_filename: string,
  url: string,
};

export default function Dashboard() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    
    try {
      await api.post("/me/photos/upload", formData);

      // Clear the file input in the upload form
      const fileInput = document.getElementById("image-input") as HTMLInputElement;
      fileInput.value = "";

      loadPhotos();
    } catch (error) {
      console.log(error);
    }
  }

  async function loadPhotos() {
    const response = await api.get("/me/photos");
    const data = response.data;
    setPhotos(data);
  }

  async function deletePhoto(photoId: string) {
    await api.delete(`/me/photos/${photoId}`);
    await loadPhotos();
  }

  useEffect(() => {
    loadPhotos();
  }, []);

  return (
    <div>
      <h3>Upload Photo</h3>
      <form onSubmit={handleSubmit}>
        <Field>
          <FieldLabel htmlFor="file">Image</FieldLabel>
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
        <Button type="submit">Upload</Button>
      </form>
      <h3>Uploaded Photos</h3>
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