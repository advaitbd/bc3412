import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import CompanyManagementPage from "./pages/CompanyManagementPage";
import PathfinderDashboardPage from "./pages/PathfinderDashboardPage";
import PathwayDisplayPage from "./pages/PathwayDisplayPage";
import NotFoundPage from "./pages/NotFoundPage";
import "./index.css"; // Ensure Tailwind is imported

function App() {
  return (
    <Router>
      {" "}
      {/* Ensure Router wraps Layout */}
      <Layout>
        <Routes>
          <Route path="/" element={<PathfinderDashboardPage />} />
          <Route path="/manage-companies" element={<CompanyManagementPage />} />
          {/* Use URL param for company name */}
          <Route
            path="/pathway/:companyName"
            element={<PathwayDisplayPage />}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
