import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import OrganizerPage from './pages/OrganizerPage';
import PlayerPage from './pages/PlayerPage';
import QuizPage from './pages/QuizPage';
import Layout from './components/Layout';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/organize" element={<OrganizerPage />} />
        <Route path="/play" element={<PlayerPage />} />
        <Route path="/quiz/:sessionId" element={<QuizPage />} />
      </Routes>
    </Layout>
  );
}
