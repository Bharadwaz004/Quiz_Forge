import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 0, // no timeout — CPU inference can take 15-20 min
});

/** Upload PDF + topic → create a quiz session */
export async function createSession(file, topic, numQuestions = 5) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('topic', topic);
  formData.append('num_questions', numQuestions);

  const { data } = await api.post('/create-session', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** Fetch session details */
export async function getSession(sessionId) {
  const { data } = await api.get(`/session/${sessionId}`);
  return data;
}

/** Join a session as a player (returns questions without answers) */
export async function joinSession(sessionId, userName) {
  const { data } = await api.post(
    `/session/${sessionId}/join?user_name=${encodeURIComponent(userName)}`
  );
  return data;
}

/** Submit an answer */
export async function submitAnswer(sessionId, userName, questionIndex, selectedAnswer) {
  const { data } = await api.post('/submit-answer', {
    session_id: sessionId,
    user_name: userName,
    question_index: questionIndex,
    selected_answer: selectedAnswer,
  });
  return data;
}

/** Fetch leaderboard */
export async function getLeaderboard(sessionId) {
  const { data } = await api.get(`/leaderboard/${sessionId}`);
  return data;
}

export default api;