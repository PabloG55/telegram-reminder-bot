import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import EditTask from './components/EditTask';
import CalendarView from './components/CalendarView';
import './index.css';
import Login from "./components/Login";



function App() {
  return (
    <Router>
      <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/edit/:id" element={<EditTask />} />
          <Route path="/calendar" element={<CalendarView />} />
          <Route path="/login" element={<Login />} />
      </Routes>
    </Router>
  );
}

export default App;