import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { getToken, logout } from "./services/auth";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(Boolean(getToken()));
  const navigate = useNavigate();

  useEffect(() => {
    const handleStorageChange = () => {
      setIsLoggedIn(Boolean(getToken()));
    };

    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  return (
    <div>
      <div>
        <nav>
          {isLoggedIn ? (
            <>
              <Link to="/">Home</Link>
              <span > | </span>
              <Link to="/jobs">Jobs</Link>
              <span > | </span>
              <button
                onClick={() => {
                  logout();
                  setIsLoggedIn(false);
                  navigate("/login");
                }} 
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <span> | </span>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </div>
      <main>
        <h1>AI Image Editor</h1>
        <p>A simple demo frontend for AI Image API</p>
      </main>
      <Outlet context={{ isLoggedIn, setIsLoggedIn }} />
    </div>
  );
}