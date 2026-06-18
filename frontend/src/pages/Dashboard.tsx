import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Link } from "react-router-dom";

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
      <div>
        <h3>Upload Photo</h3>
        <form onSubmit={handleSubmit}>
          <label htmlFor="file">Choose image to upload</label>
          <input 
            type="file"
            accept="image/*" 
            onChange={(e) => {
              if (e.target.files?.[0]) {
                setFile(e.target.files[0]);
              }
            }}
          />
          <button type="submit">Submit</button>
        </form>
      </div>
      <br />
      <h3>Uploaded Photos</h3>
      {photos.toReversed().map((photo: Photo) => (
        <div key={photo.id}>
          <img
            src={ photo.url }
            alt={ photo.original_filename }
            width="600"
          />
          <Link
            to={`/photos/${photo.id}`}
          >
            { photo.original_filename }
          </Link>
          <button onClick={() => deletePhoto(photo.id)}>
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}