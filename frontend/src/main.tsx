import ReactDOM from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Toaster } from "sonner";
import "@fontsource/inter/index.css";
import "./index.css";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import IndexRedirect from "./pages/IndexRedirect";
import Jobs from "./pages/Jobs"
import Login from "./pages/Login";
import Register from "./pages/Register";
import PhotoDetail from "./pages/PhotoDetail";
import ProtectedRoute from "./components/ProtectedRoute";
import GuestRoute from "./components/GuestRoute";

const router = createBrowserRouter([
  { 
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <IndexRedirect />},
      { 
        path: "login",
        element: (
          <GuestRoute>
            <Login />
          </GuestRoute>
        )
      },
      {
        path: "register",
        element: (
          <GuestRoute>
            <Register />
          </GuestRoute>
        )
      },
      {
        path: "photos",
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        )
      },
      {
        path: "photos/:photoId",
        element: (
          <ProtectedRoute>
            <PhotoDetail />
          </ProtectedRoute>
        )
      },
      {
        path: "jobs",
        element: (
          <ProtectedRoute>
            <Jobs />
          </ProtectedRoute>
        )
      }
    ]
  },
]);

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(
  <HelmetProvider>
    <RouterProvider router={router} />
    <Toaster richColors />
  </HelmetProvider>
);