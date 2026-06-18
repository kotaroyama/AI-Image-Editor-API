import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import IndexRedirect from "./pages/IndexRedirect";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PhotoDetail from "./pages/PhotoDetail";
import ProtectedRoute from "./components/ProtectedRoute";

const router = createBrowserRouter([
  { 
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <IndexRedirect />},
      { path: "login", element: <Login /> },
      { path: "register", element: <Register />},
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
      }
    ]
  },
]);

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(<RouterProvider router={router} />);