import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, X, ChevronRight, Loader2 } from 'lucide-react';

/**
 * QuestionCard — displays a single quiz question with options.
 * Handles selection, submission, feedback (correct/incorrect), and navigation.
 */
export default function QuestionCard({
  question,
  questionIndex,
  totalQuestions,
  onSubmit,
  onNext,
  disabled = false,
}) {
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null); // { correct, correct_answer }
  const [submitting, setSubmitting] = useState(false);

  const handleSelect = (option) => {
    if (result || submitting) return; // Lock after submit
    setSelected(option);
  };

  const handleSubmit = async () => {
    if (!selected || submitting) return;
    setSubmitting(true);

    try {
      const res = await onSubmit(questionIndex, selected);
      setResult(res);
    } catch (err) {
      console.error('Submit failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    setSelected(null);
    setResult(null);
    onNext();
  };

  const isLast = questionIndex === totalQuestions - 1;

  return (
    <motion.div
      key={questionIndex}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.35 }}
      className="card p-6 md:p-8"
    >
      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-surface-300/50">
            QUESTION {questionIndex + 1} OF {totalQuestions}
          </span>
          <span className="text-xs font-mono text-accent">
            {Math.round(((questionIndex + 1) / totalQuestions) * 100)}%
          </span>
        </div>
        <div className="h-1 bg-surface-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-accent rounded-full"
            initial={{ width: `${(questionIndex / totalQuestions) * 100}%` }}
            animate={{ width: `${((questionIndex + 1) / totalQuestions) * 100}%` }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Question text */}
      <h2 className="text-lg md:text-xl font-display font-semibold text-surface-50 leading-relaxed mb-6">
        {question.question}
      </h2>

      {/* Options */}
      <div className="space-y-3 mb-8">
        {question.options.map((option, i) => {
          const letter = String.fromCharCode(65 + i); // A, B, C, D
          const isSelected = selected === option;
          const isCorrectAnswer = result && option === result.correct_answer;
          const isWrongSelection = result && isSelected && !result.correct;

          let borderColor = 'border-surface-300/10';
          let bgColor = 'bg-transparent';
          let textColor = 'text-surface-200';
          let letterBg = 'bg-surface-800';

          if (isCorrectAnswer) {
            borderColor = 'border-correct/40';
            bgColor = 'bg-correct/5';
            textColor = 'text-correct';
            letterBg = 'bg-correct/20';
          } else if (isWrongSelection) {
            borderColor = 'border-incorrect/40';
            bgColor = 'bg-incorrect/5';
            textColor = 'text-incorrect';
            letterBg = 'bg-incorrect/20';
          } else if (isSelected && !result) {
            borderColor = 'border-accent/40';
            bgColor = 'bg-accent/5';
            textColor = 'text-accent';
            letterBg = 'bg-accent/20';
          }

          return (
            <motion.button
              key={i}
              whileHover={!result ? { scale: 1.01 } : {}}
              whileTap={!result ? { scale: 0.99 } : {}}
              onClick={() => handleSelect(option)}
              disabled={!!result || disabled}
              className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all duration-200
                ${borderColor} ${bgColor}
                ${!result && !disabled ? 'cursor-pointer hover:border-surface-300/25' : 'cursor-default'}
              `}
            >
              {/* Letter badge */}
              <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-display font-semibold flex-shrink-0
                ${letterBg} ${textColor}`}>
                {isCorrectAnswer ? <Check className="w-4 h-4" /> :
                 isWrongSelection ? <X className="w-4 h-4" /> : letter}
              </span>

              {/* Option text */}
              <span className={`text-sm md:text-base text-left flex-1 ${textColor}`}>
                {option}
              </span>
            </motion.button>
          );
        })}
      </div>

      {/* Result feedback */}
      {result && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className={`mb-6 p-4 rounded-xl border ${
            result.correct
              ? 'bg-correct/5 border-correct/20 text-correct'
              : 'bg-incorrect/5 border-incorrect/20 text-incorrect'
          }`}
        >
          <p className="font-display font-semibold text-sm">
            {result.correct ? '✓ Correct!' : '✗ Incorrect'}
          </p>
          {!result.correct && (
            <p className="text-xs mt-1 opacity-80">
              The correct answer was: {result.correct_answer}
            </p>
          )}
        </motion.div>
      )}

      {/* Action buttons */}
      <div className="flex justify-end gap-3">
        {!result ? (
          <button
            onClick={handleSubmit}
            disabled={!selected || submitting || disabled}
            className="btn-primary flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Answer'
            )}
          </button>
        ) : (
          <button onClick={handleNext} className="btn-primary flex items-center gap-2">
            {isLast ? 'View Results' : (
              <>
                Next Question
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>
    </motion.div>
  );
}
