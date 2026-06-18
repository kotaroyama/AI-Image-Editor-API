import React from "react";
import { useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";
import { api } from "../services/api";
import { saveToken } from "../services/auth";

type AuthContextType = {
  setIsLoggedIn: React.Dispatch<React.SetStateAction<boolean>>;
};

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginFailed, setLoginFailed] = useState(false);
  const { setIsLoggedIn } = useOutletContext<AuthContextType>();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await api.post("/token", formData);
        saveToken(response.data.access_token);
        setIsLoggedIn(true);
        setLoginFailed(false);
        navigate("/");
    } catch (error) {
        setLoginFailed(true);
        console.log(error);
    }
  }

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Login</button>
      </form>
      {loginFailed ? (
        <div>
          <p>Login Failed</p>
        </div>
      ) : (
        <div>
          <p>
            New to AI Image Editor?
            <span > </span>
            <Link to="/register">Sign Up</Link>
          </p>
        </div>
      )}
    </div>
  )
}