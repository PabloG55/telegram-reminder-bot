import React, { useEffect } from "react";

function Login() {
    useEffect(() => {
        // Inject Telegram login widget
        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-widget.js?7";
        script.setAttribute("data-telegram-login", "YOUR_BOT_USERNAME"); // No @
        script.setAttribute("data-size", "large");
        script.setAttribute("data-userpic", "false");
        script.setAttribute("data-request-access", "write");
        script.setAttribute("data-onauth", "handleTelegramAuth");
        script.async = true;
        document.getElementById("telegram-login-container").appendChild(script);

        // Global login callback
        window.handleTelegramAuth = (user) => {
            console.log("Telegram user:", user);

            fetch("https://whatsapp-reminder-backend.onrender.com/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(user)
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.ok) {
                        localStorage.setItem("tg_id", data.telegram_id);
                        window.location.href = `/dashboard?tg_id=${data.telegram_id}`;
                    } else {
                        alert("Login failed: " + (data.error || "unknown error"));
                    }
                })
                .catch((err) => {
                    console.error("Login error:", err);
                    alert("Something went wrong. Check console.");
                });
        };
    }, []);

    return (
        <div className="h-screen bg-gray-100 flex flex-col justify-center items-center px-4">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">Welcome to Botifier</h1>
                <p className="text-center text-gray-600 mb-4">
                    Log in with Telegram to access your task dashboard.
                </p>
                <div id="telegram-login-container" className="flex justify-center" />
            </div>
        </div>
    );
}

export default Login;