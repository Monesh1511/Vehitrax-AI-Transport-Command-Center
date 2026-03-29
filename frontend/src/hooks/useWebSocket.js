import { useEffect, useState, useRef } from 'react';

export function useWebSocket(url) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setIsConnected(true);
      setSocket(ws.current);
      console.log('WS connected to ' + url);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      setSocket(null);
      console.log('WS disconnected');
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setData(message);
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  return { data, isConnected, ws: socket };
}
