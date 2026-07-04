import { useEffect, useRef, useState, useCallback } from 'react';

function wsOrigin() {
  if (import.meta.env.PROD) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}`;
  }
  return 'ws://127.0.0.1:8001';
}

/**
 * WebSocket temps réel Coordinateur (ws/tasks/).
 * Reconnexion automatique + ping.
 */
export function useCoordinatorRealtime({ onTaskEvent, onWorkflowEvent, enabled = true } = {}) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const retryRef = useRef(0);
  const pingRef = useRef(null);
  const handlersRef = useRef({ onTaskEvent, onWorkflowEvent });
  handlersRef.current = { onTaskEvent, onWorkflowEvent };

  const disconnect = useCallback(() => {
    if (pingRef.current) {
      clearInterval(pingRef.current);
      pingRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return undefined;

    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const url = `${wsOrigin()}/ws/tasks/`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (cancelled) return;
        retryRef.current = 0;
        setConnected(true);
        ws.send(JSON.stringify({ type: 'subscribe', topics: ['tasks', 'workflows'] }));
        pingRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'task_status_changed') {
            handlersRef.current.onTaskEvent?.(msg);
          }
          if (msg.type === 'workflow_status_changed' || msg.type === 'workflow_updated') {
            handlersRef.current.onWorkflowEvent?.(msg);
          }
        } catch {
          /* ignore malformed */
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (pingRef.current) {
          clearInterval(pingRef.current);
          pingRef.current = null;
        }
        if (cancelled) return;
        const delay = Math.min(30000, 1000 * 2 ** Math.min(retryRef.current, 5));
        retryRef.current += 1;
        setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      disconnect();
    };
  }, [enabled, disconnect]);

  return { connected };
}
