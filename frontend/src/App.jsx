import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Resources from "./pages/Resources.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Savings from "./pages/Savings.jsx";
import History from "./pages/History.jsx";
import Settings from "./pages/Settings.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/resources", label: "Resources" },
  { to: "/recommendations", label: "Recommendations" },
  { to: "/savings", label: "Savings" },
  { to: "/history", label: "History" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <h1>☁️ CloudOptimizer</h1>
        <p className="tag">AWS FinOps Platform</p>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/savings" element={<Savings />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
