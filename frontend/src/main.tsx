import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import App from "./App";
import Login from "./pages/Login";
import Register from "./pages/Register";

const router = createBrowserRouter([
  { 
    path: "/",
    element: <App />,
    children: [
      { path: "login", element: <Login /> },
      { path: "register", element: <Register />},
    ]
  },
]);

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(<RouterProvider router={router} />);
