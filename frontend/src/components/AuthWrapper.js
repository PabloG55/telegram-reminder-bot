import { useEffect, useState } from "react";
import { auth } from "./firebase";
import { useNavigate, Outlet } from "react-router-dom";
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

function AuthWrapper() {
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const unsub = auth.onAuthStateChanged(async (user) => {
            if (!user) {
                navigate("/login");
            } else {
                try {
                    const res = await axios.get(`${BASE_URL}/api/user-status?uid=${user.uid}`);
                    const { telegram_connected } = res.data;

                    if (telegram_connected) {
                        setLoading(false); // ✅ allow access
                    } else {
                        // 🔒 not connected to Telegram → redirect to /welcome
                        navigate("/welcome");
                        setLoading(false);
                    }
                } catch (err) {
                    console.error("❌ Failed to verify Telegram connection:", err);
                    navigate("/welcome");
                    setLoading(false);

                }
            }
        });

        return () => unsub();
    }, [navigate]);

    if (loading) {
        return (
            <div className="h-screen flex items-center justify-center text-gray-600">
                Loading...
            </div>
        );
    }

    return <Outlet />;
}

export default AuthWrapper;
