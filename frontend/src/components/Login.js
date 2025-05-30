import React, { useEffect } from "react";
const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

function Login() {
    useEffect(() => {
        window.handleTelegramAuth = (user) => {
            console.log("✅ Telegram user:", user);

            fetch(`${BASE_URL}/api/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(user)
            })
                .then((res) => res.json())
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
                    alert("Something went wrong. Check console.");
                });
        };

        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-widget.js?7";
        script.setAttribute("data-telegram-login", "botifier5_bot");
        script.setAttribute("data-size", "large");
        script.setAttribute("data-userpic", "false");
        script.setAttribute("data-request-access", "write");
        script.setAttribute("data-onauth", "handleTelegramAuth");
        script.async = true;

        const container = document.getElementById("telegram-login-container");
        if (container) {
            container.innerHTML = "";
            container.appendChild(script);
        }
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
                <div id="telegram-login-container" className="flex justify-center" />
            </div>
        </div>
    );
}

export default Login;
