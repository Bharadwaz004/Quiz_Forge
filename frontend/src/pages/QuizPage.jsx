import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, AlertCircle, Users, Wifi, WifiOff, Trophy, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';

import { joinSession, submitAnswer, getLeaderboard } from '../lib/api';
import { useSocket } from '../hooks/useSocket';
import QuestionCard from '../components/QuestionCard';
import Leaderboard from '../components/Leaderboard';

export default function QuizPage() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  console.log('[QuizPage] Mounted. sessionId:', sessionId);
  console.log('[QuizPage] location.state:', location.state);

  // User name from navigation state, or prompt for it
  const [userName, setUserName] = useState(location.state?.userName || '');
  const [nameInput, setNameInput] = useState('');

  // Quiz state
  const [questions, setQuestions] = useState([]);
  const [topic, setTopic] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [finished, setFinished] = useState(false);
  const [myScore, setMyScore] = useState(0);

  // Socket.IO for real-time updates
  const { isConnected, players, leaderboard: liveLeaderboard } = useSocket(
    userName ? sessionId : null,
    userName
  );

  // Fallback leaderboard from API
  const [leaderboard, setLeaderboard] = useState([]);
  const effectiveLeaderboard = liveLeaderboard.length > 0 ? liveLeaderboard : leaderboard;

  // Load session data when userName is set
  useEffect(() => {
    console.log('[QuizPage useEffect] userName:', userName, 'sessionId:', sessionId);

    if (!userName) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadSession() {
      setLoading(true);
      setError(null);
      console.log('[QuizPage] Calling joinSession API...');

      try {
        const data = await joinSession(sessionId, userName);
        console.log('[QuizPage] joinSession response:', JSON.stringify(data, null, 2));
        console.log('[QuizPage] questions count:', data.questions?.length);
        console.log('[QuizPage] topic:', data.topic);

        if (!cancelled) {
          const q = data.questions || [];
          setQuestions(q);
          setTopic(data.topic || '');
          setLoading(false);

          if (q.length === 0) {
            console.error('[QuizPage] WARNING: Received 0 questions!');
            setError('No questions found in this session. The quiz may not have been generated yet.');
          }
        }
      } catch (err) {
        console.error('[QuizPage] joinSession FAILED:', err);
        console.error('[QuizPage] Error response:', err.response?.data);
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to load quiz session.');
          setLoading(false);
        }
      }
    }

    loadSession();
    return () => { cancelled = true; };
  }, [sessionId, userName]);

  // Fetch leaderboard periodically as fallback
  useEffect(() => {
    if (!userName || !sessionId) return;

    const fetchLB = async () => {
      try {
        const data = await getLeaderboard(sessionId);
        setLeaderboard(data.leaderboard || []);
      } catch (e) {
        console.log('[QuizPage] Leaderboard fetch failed (non-critical):', e.message);
      }
    };

    fetchLB();
    const interval = setInterval(fetchLB, 5000);
    return () => clearInterval(interval);
  }, [sessionId, userName]);

  // Handle answer submission
  const handleSubmit = async (questionIndex, selectedAnswer) => {
    console.log('[QuizPage] Submitting answer:', { questionIndex, selectedAnswer });
    try {
      const result = await submitAnswer(sessionId, userName, questionIndex, selectedAnswer);
      console.log('[QuizPage] Submit result:', result);
      if (result.correct) {
        setMyScore((s) => s + 1);
      }
      return result;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit answer.';
      console.error('[QuizPage] Submit failed:', msg);
      toast.error(msg);
      throw err;
    }
  };

  // Handle next question
  const handleNext = () => {
    if (currentIndex >= questions.length - 1) {
      setFinished(true);
    } else {
      setCurrentIndex((i) => i + 1);
    }
  };

  // Join with name (if not provided via navigation)
  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (nameInput.trim()) {
      console.log('[QuizPage] Setting userName:', nameInput.trim());
      setUserName(nameInput.trim());
    }
  };

  // Log current render state
  console.log('[QuizPage RENDER] userName:', userName, 'loading:', loading, 'error:', error, 'questions:', questions.length, 'finished:', finished);

  // ─── Name input screen ───
  if (!userName) {
    return (
      <div className="max-w-md mx-auto px-6 py-16">
        <div className="card p-8 text-center">
          <Users className="w-10 h-10 text-accent mx-auto mb-4" />
          <h2 className="font-display font-bold text-xl text-surface-50 mb-2">Enter Your Name</h2>
          <p className="text-sm text-surface-300/60 mb-6">
            Session: <code className="font-mono text-accent">{sessionId}</code>
          </p>
          <form onSubmit={handleNameSubmit} className="space-y-4">
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              placeholder="Your name"
              className="input-field text-center"
              autoFocus
              maxLength={50}
            />
            <button type="submit" disabled={!nameInput.trim()} className="btn-primary w-full">
              Join Quiz
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ─── Loading ───
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-accent animate-spin mx-auto mb-4" />
          <p className="text-surface-300/60 font-display">Loading quiz...</p>
        </div>
      </div>
    );
  }

  // ─── Error ───
  if (error) {
    return (
      <div className="max-w-md mx-auto px-6 py-16">
        <div className="card p-8 text-center">
          <AlertCircle className="w-10 h-10 text-incorrect mx-auto mb-4" />
          <h2 className="font-display font-bold text-xl text-surface-50 mb-2">Oops!</h2>
          <p className="text-sm text-surface-300/60 mb-6">{error}</p>
          <Link to="/play" className="btn-secondary">
            Try Another Session
          </Link>
        </div>
      </div>
    );
  }

  // ─── No questions guard ───
  if (questions.length === 0) {
    return (
      <div className="max-w-md mx-auto px-6 py-16">
        <div className="card p-8 text-center">
          <AlertCircle className="w-10 h-10 text-accent mx-auto mb-4" />
          <h2 className="font-display font-bold text-xl text-surface-50 mb-2">No Questions</h2>
          <p className="text-sm text-surface-300/60 mb-6">
            This session has no questions yet. It may still be generating.
          </p>
          <button onClick={() => window.location.reload()} className="btn-primary">
            Refresh
          </button>
        </div>
      </div>
    );
  }

  // ─── Current question guard ───
  const currentQuestion = questions[currentIndex];
  if (!currentQuestion) {
    console.error('[QuizPage] currentQuestion is undefined! index:', currentIndex, 'total:', questions.length);
    return (
      <div className="max-w-md mx-auto px-6 py-16">
        <div className="card p-8 text-center">
          <AlertCircle className="w-10 h-10 text-incorrect mx-auto mb-4" />
          <h2 className="font-display font-bold text-xl text-surface-50 mb-2">Something went wrong</h2>
          <p className="text-sm text-surface-300/60 mb-6">
            Question {currentIndex + 1} not found. (Total: {questions.length})
          </p>
          <button onClick={() => window.location.reload()} className="btn-primary">
            Refresh
          </button>
        </div>
      </div>
    );
  }

  // ─── Finished ───
  if (finished) {
    const myEntry = effectiveLeaderboard.find((e) => e.user_name === userName);
    const rank = effectiveLeaderboard.findIndex((e) => e.user_name === userName) + 1;

    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card p-8 text-center mb-8"
        >
          <Trophy className="w-14 h-14 text-accent mx-auto mb-4" />
          <h2 className="font-display font-bold text-3xl text-surface-50 mb-2">Quiz Complete!</h2>
          <p className="text-surface-300/60 mb-6">{topic}</p>

          <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto mb-6">
            <div className="bg-surface-950 rounded-xl p-4 border border-surface-300/10">
              <p className="text-2xl font-display font-bold text-accent">{myScore}</p>
              <p className="text-xs text-surface-300/50">Score</p>
            </div>
            <div className="bg-surface-950 rounded-xl p-4 border border-surface-300/10">
              <p className="text-2xl font-display font-bold text-surface-100">{questions.length}</p>
              <p className="text-xs text-surface-300/50">Questions</p>
            </div>
            <div className="bg-surface-950 rounded-xl p-4 border border-surface-300/10">
              <p className="text-2xl font-display font-bold text-surface-100">
                {myEntry ? `${myEntry.accuracy}%` : `${Math.round((myScore / questions.length) * 100)}%`}
              </p>
              <p className="text-xs text-surface-300/50">Accuracy</p>
            </div>
          </div>

          {rank > 0 && (
            <p className="text-sm text-surface-300/60">
              You placed <span className="text-accent font-display font-semibold">#{rank}</span> out of {effectiveLeaderboard.length} players
            </p>
          )}
        </motion.div>

        <Leaderboard
          entries={effectiveLeaderboard}
          totalQuestions={questions.length}
          currentUser={userName}
        />

        <div className="flex justify-center gap-3 mt-8">
          <Link to="/" className="btn-secondary flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            Back Home
          </Link>
        </div>
      </div>
    );
  }

  // ─── Quiz in progress ───
  return (
    <div className="max-w-5xl mx-auto px-6 py-8 md:py-12">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display font-bold text-xl text-surface-50">{topic}</h1>
          <p className="text-sm text-surface-300/50 mt-0.5">
            Playing as <span className="text-accent font-medium">{userName}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="badge bg-surface-800 text-surface-300/60">
            <Users className="w-3.5 h-3.5 mr-1.5" />
            {players.length || 1}
          </div>
          <div className={`badge ${isConnected ? 'bg-correct/10 text-correct' : 'bg-incorrect/10 text-incorrect'}`}>
            {isConnected ? <Wifi className="w-3.5 h-3.5 mr-1" /> : <WifiOff className="w-3.5 h-3.5 mr-1" />}
            {isConnected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>

      {/* Main layout: question + sidebar */}
      <div className="grid lg:grid-cols-[1fr_320px] gap-6 items-start">
        {/* Question area */}
        <div>
          <AnimatePresence mode="wait">
            <QuestionCard
              key={currentIndex}
              question={currentQuestion}
              questionIndex={currentIndex}
              totalQuestions={questions.length}
              onSubmit={handleSubmit}
              onNext={handleNext}
            />
          </AnimatePresence>
        </div>

        {/* Sidebar: leaderboard */}
        <div className="hidden lg:block sticky top-24">
          <Leaderboard
            entries={effectiveLeaderboard}
            totalQuestions={questions.length}
            currentUser={userName}
          />
        </div>
      </div>
    </div>
  );
}