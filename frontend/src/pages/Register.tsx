import axios from "axios";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { 
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label"

import { api } from "../services/api";

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
      <Card>
        <CardHeader>
          <CardTitle>Register</CardTitle>
          <CardDescription>
            Sign up with your email
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Label htmlFor="username">Username</Label>
            <Input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <Label htmlFor="email">Email</Label>
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit">Register</Button>
          </form>
        </CardContent>
      </Card>
      {error && <p>{error}</p>}
      {status ? (
        <div>
          <h3>Sign up successful!</h3>
        </div>
      ) : (
        <div className="text-center text-sm text-muted-foreground">
          Already have an acccount?{" "}
          <Link 
            to="/login"
            className="font-medium text-primary hover:underline"
          >
            Login
          </Link>
        </div>
      )}
    </div>
  );
}