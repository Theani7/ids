import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';
const MAX_ALERTS = 100;
const MAX_RECONNECT_DELAY = 30000;

export default function useWebSocket() {
  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState({ total: 0, malicious: 0, normal: 0 });

  const wsRef = useRef(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);
  const reconnectTimerRef = useRef(null);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setStats({ total: 0, malicious: 0, normal: 0 });
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        attemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const data = JSON.parse(event.data);

          setAlerts((prev) => {
            const next = [data, ...prev];
            return next.length > MAX_ALERTS ? next.slice(0, MAX_ALERTS) : next;
          });

          setStats((prev) => ({
            total: prev.total + 1,
            malicious:
              data.label === 'MALICIOUS' ? prev.malicious + 1 : prev.malicious,
            normal:
              data.label === 'NORMAL' ? prev.normal + 1 : prev.normal,
          }));
        } catch {
          // ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setIsConnected(false);

        // Exponential back-off reconnect
        attemptRef.current += 1;
        const delay = Math.min(
          2000 * attemptRef.current,
          MAX_RECONNECT_DELAY,
        );
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // onclose will fire after this
      };
    } catch {
      // Will retry via the reconnect logic in onclose
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { alerts, isConnected, stats, clearAlerts };
}
