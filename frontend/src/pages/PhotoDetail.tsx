import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";

type Photo = {
  id: string,
  original_filename: string,
  url: string,
};

export default function PhotoDetail() {
  const navigate = useNavigate();

  const { photoId } = useParams();
  const [photo, setPhoto] = useState<Photo>();

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

  useEffect(() => {
    loadPhoto();
  }, [photoId])

  return (
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
  )
}