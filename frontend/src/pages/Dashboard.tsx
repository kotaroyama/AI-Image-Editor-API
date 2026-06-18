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
      <h2>Uploaded Photos</h2>
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