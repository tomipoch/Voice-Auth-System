import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EnrollmentPage from './pages/EnrollmentPage';
import TransferPage from './pages/TransferPage';
import VerificationPage from './pages/VerificationPage';
import ResultPage from './pages/ResultPage';
import ProfilePage from './pages/ProfilePage';
import SetupPinPage from './pages/SetupPinPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/enroll" element={<EnrollmentPage />} />
        <Route path="/transfer" element={<TransferPage />} />
        <Route path="/verify" element={<VerificationPage />} />
        <Route path="/result" element={<ResultPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/setup-pin" element={<SetupPinPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
