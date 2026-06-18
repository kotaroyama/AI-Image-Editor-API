import { Navigate } from "react-router-dom";
import { getToken } from "../services/auth";

export default function IndexRedirect() {
    const isLoggedIn = Boolean(getToken());

    return isLoggedIn ? (
      <Navigate to="/photos" replace />
    ) : (
      <Navigate to="/login" replace />
    );
}