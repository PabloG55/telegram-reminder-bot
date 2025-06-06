import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signInWithPopup, signInWithEmailAndPassword } from "firebase/auth";
import { auth, googleProvider } from "./firebase";
import axios from "axios";
const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";


function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = async (user) => {
        try {
            const res = await axios.get(`${BASE_URL}/api/user-status?uid=${user.uid}`);
            const { telegram_connected } = res.data;

            if (telegram_connected) {
                navigate("/dashboard"); // ✅ skip Telegram connect
            } else {
                window.open("/welcome"); // ask them to connect Telegram
            }
        } catch (err) {
            console.error("❌ Failed to fetch Telegram status:", err);
            window.open("/welcome"); // fallback
        }
    };

    const handleGoogleLogin = async () => {
        try {
            const result = await signInWithPopup(auth, googleProvider);
            const user = result.user;
            console.log("✅ Google user:", user.email);
            await handleLogin(user);
        } catch (err) {
            alert("❌ " + err.message);
        }
    };

    const handleEmailLogin = async () => {
        try {
            const result = await signInWithEmailAndPassword(auth, email, password);
            const user = result.user;
            console.log("✅ Email user:", user.email);
            await handleLogin(user);
        } catch (err) {
            alert("❌ " + err.message);
        }
    };


    return (
        <div className="h-screen bg-gray-100 flex flex-col justify-center items-center px-4">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">
                    Welcome to Botifier
                </h1>
                <p className="text-center text-gray-600 mb-4">
                    Log in with Email or Google to access your task dashboard.
                </p>

                {/* Email Input */}
                <input
                    type="email"
                    placeholder="Email"
                    className="w-full mb-3 p-2 border rounded"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />

                {/* Password Input */}
                <input
                    type="password"
                    placeholder="Password"
                    className="w-full mb-4 p-2 border rounded"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />

                {/* Email Login Button */}
                <div className="mt-6">
                    <button
                        onClick={handleEmailLogin}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded mb-4"
                    >
                        Log in with Email
                    </button>
                    <p className="text-sm text-center text-gray-600 mt-4">
                        Don’t have an account?{" "}
                        <a
                            href="/register"
                            className="text-blue-600 hover:underline font-medium"
                        >
                            Register here
                        </a>
                    </p>
                </div>

                <div className="mt-6">
                    <div className="flex items-center my-6">
                        <div className="flex-grow h-px bg-gray-300" />
                        <span className="mx-3 text-gray-500 text-sm">or</span>
                        <div className="flex-grow h-px bg-gray-300" />
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-md py-2 hover:bg-gray-50 transition-colors"
                    >
                        <img
                            src="https://www.svgrepo.com/show/475656/google-color.svg"
                            alt="Google logo"
                            className="h-5 w-5"
                        />
                        <span className="text-gray-700 font-medium">Continue with Google</span>
                    </button>


                </div>

            </div>
        </div>
    );
}

export default Login;
