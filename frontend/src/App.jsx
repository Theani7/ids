import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LiveTracker from './pages/LiveTracker';
import BatchAnalyzer from './pages/BatchAnalyzer';
import Navigation from './components/Navigation';

const DashboardLayout = ({ children }) => {
  return (
    <div className="flex h-screen bg-netbg overflow-hidden">
      <Navigation />
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-netbg text-[#e6edf3] font-mono">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          
          <Route path="/live" element={
            <DashboardLayout>
              <LiveTracker />
            </DashboardLayout>
          } />
          <Route path="/batch" element={
            <DashboardLayout>
              <BatchAnalyzer />
            </DashboardLayout>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
