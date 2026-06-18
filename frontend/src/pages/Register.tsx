import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import axios from "axios";

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    
    try {
      await api.post("/register", {
        username,
        email,
        password,
      });
      setStatus(true);
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 400) {
                setError("Username or Email already exists");
            } else {
                setError("Registration failed");
            }
        } else {
            setError("An unexpected error occurred");
        }
        
        setUsername("");
        setPassword("");
    }
  }

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Register</button>
      </form>
      {error && <p>{error}</p>}
      {status ? (
        <div>
          <h3>Sign up successful!</h3>
        </div>
      ) : (
        <div>
          <p>
            Already have an acccount?
            <Link to="/login">Login</Link>
          </p>
        </div>
      )}
    </div>
  );
}