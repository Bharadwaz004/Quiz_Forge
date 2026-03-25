import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Loader2, Copy, CheckCheck, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { createSession } from '../lib/api';

export default function OrganizerPage() {
  const [file, setFile] = useState(null);
  const [topic, setTopic] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [session, setSession] = useState(null);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped?.type === 'application/pdf') {
      setFile(dropped);
    } else {
      toast.error('Please upload a PDF file.');
    }
  };

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !topic.trim()) return;

    setLoading(true);
    setSession(null);

    const messages = [
      'Extracting text from PDF...',
      'Chunking document...',
      'Generating embeddings...',
      'Retrieving relevant context...',
      'Generating quiz questions with LLM...',
      'Validating output...',
    ];

    let msgIndex = 0;
    setLoadingMessage(messages[0]);
    const interval = setInterval(() => {
      msgIndex = Math.min(msgIndex + 1, messages.length - 1);
      setLoadingMessage(messages[msgIndex]);
    }, 4000);

    try {
      const result = await createSession(file, topic.trim(), numQuestions);
      setSession(result);
      toast.success(`Quiz created with ${result.num_questions} questions!`);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to create session.';
      toast.error(message);
    } finally {
      clearInterval(interval);
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const copySessionId = () => {
    if (session?.session_id) {
      navigator.clipboard.writeText(session.session_id);
      setCopied(true);
      toast.success('Session ID copied!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 md:py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="font-display font-bold text-3xl text-surface-50 mb-2">Create a Quiz</h1>
        <p className="text-surface-300/60 mb-10">Upload a PDF and specify a topic — the AI will generate questions.</p>
      </motion.div>

      <AnimatePresence mode="wait">
        {!session ? (
          <motion.form
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            {/* File upload zone */}
            <div>
              <label className="label">PDF Document</label>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`card p-8 text-center cursor-pointer transition-all duration-200 border-dashed
                  ${file ? 'border-accent/30 bg-accent/5' : 'hover:border-surface-300/25 hover:bg-surface-900/50'}`}
              >
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-6 h-6 text-accent" />
                    <div className="text-left">
                      <p className="text-sm font-display font-medium text-surface-100">{file.name}</p>
                      <p className="text-xs text-surface-300/50">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-surface-300/30 mx-auto mb-3" />
                    <p className="text-sm text-surface-300/60">
                      Drop a PDF here or <span className="text-accent underline">browse</span>
                    </p>
                    <p className="text-xs text-surface-300/30 mt-1">Max 20 MB</p>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>

            {/* Topic */}
            <div>
              <label className="label" htmlFor="topic">Quiz Topic</label>
              <input
                id="topic"
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Machine Learning Fundamentals"
                className="input-field"
                required
                minLength={2}
                maxLength={200}
              />
            </div>

            {/* Num questions */}
            <div>
              <label className="label" htmlFor="numQ">Number of Questions</label>
              <input
                id="numQ"
                type="number"
                value={numQuestions}
                onChange={(e) => setNumQuestions(Math.max(1, Math.min(20, +e.target.value)))}
                min={1}
                max={20}
                className="input-field w-32"
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!file || !topic.trim() || loading}
              className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {loadingMessage}
                </>
              ) : (
                'Generate Quiz'
              )}
            </button>
          </motion.form>
        ) : (
          /* ─── Session Created ─── */
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="card p-8 text-center">
              <div className="w-14 h-14 rounded-2xl bg-correct/10 border border-correct/20 flex items-center justify-center mx-auto mb-5">
                <CheckCheck className="w-7 h-7 text-correct" />
              </div>
              <h2 className="font-display font-bold text-xl text-surface-50 mb-2">Quiz Ready!</h2>
              <p className="text-surface-300/60 text-sm mb-6">
                {session.num_questions} questions generated for "{session.topic}"
              </p>

              {/* Session ID */}
              <div className="bg-surface-950 rounded-xl p-4 border border-surface-300/10 mb-4">
                <p className="text-xs font-mono text-surface-300/40 mb-1.5">SESSION ID</p>
                <div className="flex items-center justify-center gap-3">
                  <code className="font-mono text-2xl font-bold text-accent tracking-wider">
                    {session.session_id}
                  </code>
                  <button
                    onClick={copySessionId}
                    className="p-2 rounded-lg hover:bg-surface-800 transition-colors"
                    title="Copy session ID"
                  >
                    {copied ? (
                      <CheckCheck className="w-5 h-5 text-correct" />
                    ) : (
                      <Copy className="w-5 h-5 text-surface-300/50" />
                    )}
                  </button>
                </div>
                <p className="text-xs text-surface-300/40 mt-2">Share this code with participants</p>
              </div>
            </div>

            {/* Questions preview */}
            <div className="card p-6">
              <h3 className="font-display font-semibold text-surface-200 mb-4">Questions Preview</h3>
              <div className="space-y-3">
                {session.questions.map((q, i) => (
                  <div key={i} className="flex gap-3 py-2 border-b border-surface-300/5 last:border-0">
                    <span className="w-6 h-6 rounded-md bg-surface-800 flex items-center justify-center text-xs font-mono text-surface-300/60 flex-shrink-0">
                      {i + 1}
                    </span>
                    <p className="text-sm text-surface-200/80 leading-relaxed">{q.question}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button onClick={() => { setSession(null); setFile(null); setTopic(''); }} className="btn-secondary flex-1">
                Create Another
              </button>
              <a
                href={`/quiz/${session.session_id}`}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                Open Quiz <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
