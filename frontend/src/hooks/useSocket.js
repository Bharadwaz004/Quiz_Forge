import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

/**
 * useSocket — manages a Socket.IO connection for a quiz session.
 *
 * Returns: { socket, players, leaderboard, isConnected, joinRoom }
 */
export function useSocket(sessionId, userName) {
  const socketRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [players, setPlayers] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [activityFeed, setActivityFeed] = useState([]);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[Socket] Connected:', socket.id);
      setIsConnected(true);

      // Auto-join room if session + user provided
      if (sessionId && userName) {
        socket.emit('join_session', {
          session_id: sessionId,
          user_name: userName,
        });
      }
    });

    socket.on('disconnect', () => {
      console.log('[Socket] Disconnected');
      setIsConnected(false);
    });

    socket.on('player_joined', (data) => {
      console.log('[Socket] Player joined:', data.user_name);
      setPlayers(data.players || []);
    });

    socket.on('player_left', (data) => {
      console.log('[Socket] Player left:', data.user_name);
      setPlayers(data.players || []);
    });

    socket.on('leaderboard_update', (data) => {
      console.log('[Socket] Leaderboard update:', data.leaderboard?.length, 'entries');
      setLeaderboard(data.leaderboard || []);
    });

    socket.on('answer_submitted', (data) => {
      setActivityFeed((prev) => [
        { user: data.user_name, question: data.question_index, time: Date.now() },
        ...prev.slice(0, 19), // keep last 20 items
      ]);
    });

    socket.on('error', (data) => {
      console.error('[Socket] Error:', data.message);
    });

    return () => {
      if (sessionId) {
        socket.emit('leave_session', { session_id: sessionId });
      }
      socket.disconnect();
    };
  }, [sessionId, userName]);

  const joinRoom = useCallback(
    (sid, uname) => {
      if (socketRef.current?.connected) {
        socketRef.current.emit('join_session', {
          session_id: sid,
          user_name: uname,
        });
      }
    },
    []
  );

  return {
    socket: socketRef.current,
    isConnected,
    players,
    leaderboard,
    activityFeed,
    joinRoom,
  };
}
