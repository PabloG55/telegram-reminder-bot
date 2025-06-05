import { useEffect, useState } from "react";
import { auth } from "./firebase";
import { useNavigate } from "react-router-dom";

function Welcome() {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [connectCopied, setConnectCopied] = useState(false);

    const tg_id = new URLSearchParams(window.location.search).get("tg_id") || localStorage.getItem("tg_id");

    useEffect(() => {
        const unsub = auth.onAuthStateChanged(async (u) => {
            setUser(u);
            if (u) {
                try {
                    const res = await fetch(`${process.env.REACT_APP_API_URL}/api/firebase-login`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid: u.uid, email: u.email }),
                    });
                    const data = await res.json();
                    console.log("✅ Firebase user registered:", data);
                } catch (err) {
                    console.error("❌ Failed to register Firebase user:", err);
                }
            }
        });

        return () => unsub();
    }, []);

    useEffect(() => {
        if (tg_id) {
            localStorage.setItem("tg_id", tg_id);
            navigate("/dashboard");
        }
    }, [tg_id, navigate]);

    if (!user) {
        return (
            <div className="h-screen flex items-center justify-center text-gray-600">
                Loading user...
            </div>
        );
    }

    const handleConnect = () => {
        const uid = user.uid;
        const command = `/connect ${uid}`;
        navigator.clipboard.writeText(command);
        setConnectCopied(true);

        // Open Telegram in a new tab
        window.open("https://web.telegram.org/k/#@botifier5_bot");

        // Wait 10 seconds, then close the current (Botifier Welcome) tab
        setTimeout(() => {
            window.close();
        }, 5000); // 10 seconds
    };


    return (
        <div className="h-screen flex flex-col justify-center items-center text-center px-4 bg-gray-50">
            <h1 className="text-3xl font-bold mb-4">Hello, {user.displayName || user.email} 👋</h1>
            <p className="mb-4 text-gray-600">To continue, connect your Telegram account.</p>

            <button
                onClick={handleConnect}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded shadow"
            >
                Connect to Telegram
            </button>

            {connectCopied && (
                <p className="mt-4 text-green-600 text-sm">
                    ✅ Command <code className="bg-gray-200 px-2 py-1 rounded">{`/connect ${user.uid}`}</code> copied! Paste it in Telegram.
                </p>
            )}
        </div>
    );
}

export default Welcome;
