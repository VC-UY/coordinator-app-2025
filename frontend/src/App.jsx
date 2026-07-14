import { Routes, Route } from 'react-router'
import './App.css'
import Home from './components/Home';
import Manager from './components/Manager'
import Volunteer from './components/Volunteer'
import Workflows from './components/Workflows';
import Tasks from './components/Tasks';
import Analytics from './components/Analytics';
import SystemStatus from './components/SystemStatus';
import AvailabilityPredictions from './components/AvailabilityPredictions';
import Navbar from './components/navbar/Navbar'
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const protectedContent = (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/manager" element={<Manager />} />
      <Route path="/volunteer" element={<Volunteer />} />
      <Route path="/workflows" element={<Workflows />} />
      <Route path="/tasks" element={<Tasks />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/predictions" element={<AvailabilityPredictions />} />
      <Route path="/system-status" element={<SystemStatus />} />
    </Routes>
  );

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={(
          <ProtectedRoute>
            <Navbar content={protectedContent} />
          </ProtectedRoute>
        )}
      />
    </Routes>
  );
}

export default App
