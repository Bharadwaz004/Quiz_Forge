import { Trophy, Medal, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Leaderboard({ entries = [], totalQuestions = 0, currentUser = '' }) {
  if (!entries.length) {
    return (
      <div className="card p-6 text-center">
        <Trophy className="w-10 h-10 text-surface-300/30 mx-auto mb-3" />
        <p className="text-sm text-surface-300/60 font-display">No scores yet</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-300/10 flex items-center gap-2.5">
        <Trophy className="w-5 h-5 text-accent" />
        <h3 className="font-display font-semibold text-surface-100">Leaderboard</h3>
        <span className="badge bg-accent/10 text-accent ml-auto">
          {entries.length} player{entries.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Entries */}
      <div className="divide-y divide-surface-300/5">
        <AnimatePresence mode="popLayout">
          {entries.map((entry, i) => (
            <motion.div
              key={entry.user_name}
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.25, delay: i * 0.04 }}
              className={`flex items-center gap-4 px-5 py-3.5 transition-colors
                ${entry.user_name === currentUser ? 'bg-accent/5' : 'hover:bg-surface-800/40'}`}
            >
              {/* Rank */}
              <div className="w-8 flex-shrink-0">
                {i === 0 ? (
                  <span className="text-lg">🥇</span>
                ) : i === 1 ? (
                  <span className="text-lg">🥈</span>
                ) : i === 2 ? (
                  <span className="text-lg">🥉</span>
                ) : (
                  <span className="text-sm font-mono text-surface-300/50 text-center block">
                    {i + 1}
                  </span>
                )}
              </div>

              {/* Name */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-display font-medium truncate
                  ${entry.user_name === currentUser ? 'text-accent' : 'text-surface-100'}`}>
                  {entry.user_name}
                  {entry.user_name === currentUser && (
                    <span className="text-xs text-accent/60 ml-1.5">(you)</span>
                  )}
                </p>
                <p className="text-xs text-surface-300/50 mt-0.5">
                  {entry.total_answered}/{totalQuestions} answered
                </p>
              </div>

              {/* Accuracy */}
              <div className="text-right flex-shrink-0">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-surface-300/40" />
                  <span className="text-xs text-surface-300/60">{entry.accuracy}%</span>
                </div>
              </div>

              {/* Score */}
              <div className="w-14 flex-shrink-0 text-right">
                <motion.span
                  key={entry.score}
                  initial={{ scale: 1.3, color: '#e85d26' }}
                  animate={{ scale: 1, color: '#f0efe8' }}
                  transition={{ duration: 0.3 }}
                  className="text-lg font-display font-bold"
                >
                  {entry.score}
                </motion.span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
