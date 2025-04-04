import React from "react";
import { Link, useLocation } from "react-router-dom";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Pathfinder Dashboard" },
    { path: "/manage-companies", label: "Manage Companies" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white shadow-md">
        <nav className="container mx-auto px-6 py-3 flex justify-between items-center">
          <div className="text-xl font-semibold">
            Energy Transition Pathfinder
          </div>
          <div>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === item.path
                    ? "bg-gray-900 text-white"
                    : "text-gray-300 hover:bg-gray-700 hover:text-white"
                } ${item.path !== "/" ? "ml-4" : ""}`} // Add margin only for non-first items
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      </header>
      <main className="flex-grow container mx-auto px-6 py-8">{children}</main>
      <footer className="bg-gray-200 text-center p-4 text-sm text-gray-600 mt-8">
        © {new Date().getFullYear()} Energy Transition Analysis Tool
      </footer>
    </div>
  );
};

export default Layout;
