import React from "react";
import { useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";

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
      <Card>
        <CardHeader>
          <CardTitle>Login to your acount</CardTitle>
          <CardDescription>
            Enter your username to loging to your account
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
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit">Login</Button>
          </form>
        </CardContent>
      </Card>
      {loginFailed ? (
        <div>
          <p>Login Failed</p>
        </div>
      ) : (
        <div className="text-center text-sm text-muted-foreground">
          New to AI Image Editor?{" "}
          <Link
            to="/register"
            className="font-medium text-primary hover:underline"
          >
            Sign Up
          </Link>
        </div>
      )}
    </div>
  )
}