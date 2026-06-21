import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button"

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
  <div className="min-h-screen bg-background text-foreground">
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="text-xl font-bold tracking-tight">
          AI Image Editor
        </Link>

        <nav className="flex items-center gap-2">
          {isLoggedIn ? (
            <>
              <Button variant="ghost" asChild>
                <Link to="/">Uploaded</Link>
              </Button>

              <Button variant="ghost" asChild>
                <Link to="/jobs">Edited</Link>
              </Button>

              <Button
                variant="outline"
                onClick={() => {
                  logout();
                  setIsLoggedIn(false);
                  navigate("/login");
                }}
              >
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" asChild>
                <Link to="/login">Login</Link>
              </Button>

              <Button asChild>
                <Link to="/register">Register</Link>
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>

    <main className="mx-auto max-w-6xl px-4 py-8">
      <section className="mb-8 space-y-2">
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
          AI Image Editor
        </h1>

        <p className="text-muted-foreground">
          Upload, edit, and download AI-enhanced images.
        </p>
      </section>

      <Outlet context={{ isLoggedIn, setIsLoggedIn }} />
    </main>
  </div>
);
}