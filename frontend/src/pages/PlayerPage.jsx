import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, ArrowRight, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { joinSession } from '../lib/api';

export default function PlayerPage() {
  const [sessionId, setSessionId] = useState('');
  const [userName, setUserName] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleJoin = async (e) => {
    e.preventDefault();
    if (!sessionId.trim() || !userName.trim()) return;

    setLoading(true);
    try {
      await joinSession(sessionId.trim(), userName.trim());
      // Navigate to the quiz page with user info in state
      navigate(`/quiz/${sessionId.trim()}`, {
        state: { userName: userName.trim() },
      });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not join session.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-16 md:py-24">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-5">
          <Users className="w-7 h-7 text-accent" />
        </div>
        <h1 className="font-display font-bold text-3xl text-surface-50 mb-2">Join a Quiz</h1>
        <p className="text-surface-300/60">Enter the session code from your organizer.</p>
      </motion.div>

      <motion.form
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        onSubmit={handleJoin}
        className="space-y-5"
      >
        <div>
          <label className="label" htmlFor="sessionId">Session ID</label>
          <input
            id="sessionId"
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="e.g. a1b2c3d4e5f6"
            className="input-field text-center font-mono text-lg tracking-wider"
            required
            autoFocus
          />
        </div>

        <div>
          <label className="label" htmlFor="userName">Your Name</label>
          <input
            id="userName"
            type="text"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            placeholder="e.g. Alice"
            className="input-field"
            required
            maxLength={50}
          />
        </div>

        <button
          type="submit"
          disabled={!sessionId.trim() || !userName.trim() || loading}
          className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Joining...
            </>
          ) : (
            <>
              Join Quiz
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </motion.form>
    </div>
  );
}
