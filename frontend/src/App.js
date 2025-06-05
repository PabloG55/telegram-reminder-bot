import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import EditTask from './components/EditTask';
import CalendarView from './components/CalendarView';
import Login from "./components/Login";
import Register from "./components/Register";
import AuthWrapper from "./components/AuthWrapper";
import './index.css';
import Welcome from "./components/Welcome";

function App() {
    return (
        <Router>
            <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Routes */}
                <Route element={<AuthWrapper />}>
                    <Route path="/welcome" element={<Welcome />} />
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/edit/:id" element={<EditTask />} />
                    <Route path="/calendar" element={<CalendarView />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
