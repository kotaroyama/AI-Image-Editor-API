import React from "react";
import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useNavigate, useOutletContext } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { 
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
    <div className="flex justify-center px-4 py-8">
      <Helmet>
        <title>Login | AI Image Editor</title>
      </Helmet>

      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">
            Login
          </CardTitle>
          <CardDescription>
            Enter your username to loging to your account
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {loginFailed && (
              <p className="text-sm text-desctructive">
                Invalid username or password.
              </p>
            )}
            <Button 
              type="submit"
              className="w-full"
            >
              Login
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            New to AI Image Editor?{" "}
            <Link
              to="/register"
              className="font-medium text-primary hover:underline"
            >
              Sign Up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}