import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen, Users, Zap, Brain, Shield, BarChart3 } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-16 md:py-24">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-20"
      >
        <div className="inline-flex items-center gap-2 badge bg-accent/10 text-accent border border-accent/20 mb-6 px-4 py-1.5">
          <Zap className="w-3.5 h-3.5" />
          <span>RAG-Powered Quiz Generation</span>
        </div>

        <h1 className="font-display font-bold text-4xl md:text-6xl text-surface-50 tracking-tight leading-tight mb-6">
          Upload a document.
          <br />
          <span className="text-accent">Quiz your team.</span>
        </h1>

        <p className="text-lg text-surface-300/70 max-w-2xl mx-auto leading-relaxed mb-10">
          QuizForge uses Retrieval-Augmented Generation to create quiz questions
          directly from your documents. No hallucinations — every question is
          grounded in your content.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/organize" className="btn-primary text-base px-8 py-3.5 flex items-center gap-2.5">
            <BookOpen className="w-5 h-5" />
            Create a Quiz
          </Link>
          <Link to="/play" className="btn-secondary text-base px-8 py-3.5 flex items-center gap-2.5">
            <Users className="w-5 h-5" />
            Join a Session
          </Link>
        </div>
      </motion.div>

      {/* Features grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {[
          {
            icon: Brain,
            title: 'RAG-Powered',
            desc: 'Questions generated exclusively from your uploaded document using context retrieval and local LLMs.',
          },
          {
            icon: Shield,
            title: 'Anti-Hallucination',
            desc: 'Three-layer guardrails ensure the AI never fabricates answers. Strict context-only generation.',
          },
          {
            icon: BarChart3,
            title: 'Live Leaderboard',
            desc: 'Real-time scoring via WebSockets. Multiple players compete simultaneously with instant rankings.',
          },
        ].map((feat, i) => (
          <motion.div
            key={feat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 + i * 0.1 }}
            className="card p-6 group"
          >
            <div className="w-11 h-11 rounded-xl bg-accent/8 border border-accent/15 flex items-center justify-center mb-4 group-hover:bg-accent/15 transition-colors">
              <feat.icon className="w-5 h-5 text-accent" />
            </div>
            <h3 className="font-display font-semibold text-surface-100 mb-2">{feat.title}</h3>
            <p className="text-sm text-surface-300/60 leading-relaxed">{feat.desc}</p>
          </motion.div>
        ))}
      </div>

      {/* Architecture note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-16 text-center"
      >
        <p className="text-xs font-mono text-surface-300/30 tracking-wide">
          FASTAPI · REACT · MONGODB · CHROMADB · SOCKET.IO · SENTENCE-TRANSFORMERS
        </p>
      </motion.div>
    </div>
  );
}
