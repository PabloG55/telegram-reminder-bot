import { useEffect, useState } from "react";
import { auth } from "./firebase";
import { useNavigate, Outlet } from "react-router-dom";

function AuthWrapper() {
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const unsub = auth.onAuthStateChanged((user) => {
            if (!user) {
                navigate("/login");
            } else {
                setLoading(false);
            }
        });

        if (auth.currentUser) {
            setLoading(false);
        }

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
