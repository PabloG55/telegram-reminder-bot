import React, { useEffect } from "react";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

function Login() {
    useEffect(() => {
        const container = document.getElementById("telegram-login-container");
        if (container) {
            container.innerHTML = "";
        }

        // Define the callback function globally
        window.handleTelegramAuth = (user) => {
            console.log("✅ Telegram user:", user);

            fetch(`${BASE_URL}/api/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(user),
                credentials: 'include'
            })
                .then((res) => {
                    console.log("Response status:", res.status);
                    return res.json();
                })
                .then((data) => {
                    console.log("🎯 Response from backend:", data);
                    if (data.ok) {
                        localStorage.setItem("tg_id", data.telegram_id);
                        window.location.href = "/dashboard";
                    } else {
                        alert("Login failed: " + (data.error || "unknown error"));
                    }
                })
                .catch((err) => {
                    console.error("❌ Login error:", err);
                    alert("Something went wrong. Check console for details.");
                });
        };

        // Small delay to ensure DOM is ready
        setTimeout(() => {
            const script = document.createElement("script");
            script.src = "https://telegram.org/js/telegram-widget.js?22"; // Updated version
            script.setAttribute("data-telegram-login", "botifier5_bot");
            script.setAttribute("data-size", "large");
            script.setAttribute("data-userpic", "false");
            script.setAttribute("data-request-access", "write");
            script.setAttribute("data-onauth", "handleTelegramAuth(user)"); // Fixed syntax
            script.async = true;

            // Error handling for script loading
            script.onerror = () => {
                console.error("Failed to load Telegram widget script");
                alert("Failed to load Telegram login widget. Please check your internet connection.");
            };

            script.onload = () => {
                console.log("Telegram widget script loaded successfully");
            };

            const container = document.getElementById("telegram-login-container");
            if (container) {
                container.appendChild(script);
            } else {
                console.error("telegram-login-container not found");
            }
        }, 100);

        return () => {
            if (window.handleTelegramAuth) {
                delete window.handleTelegramAuth;
            }
        };
    }, []);

    return (
        <div className="h-screen bg-gray-100 flex flex-col justify-center items-center px-4">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">
                    Welcome to Botifier
                </h1>
                <p className="text-center text-gray-600 mb-4">
                    Log in with Telegram to access your task dashboard.
                </p>

                <div id="telegram-login-container" className="flex justify-center min-h-[50px]">
                    <div className="text-center text-gray-500">
                        Loading Telegram login...
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Login;