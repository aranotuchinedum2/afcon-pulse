// hooks/useAfconData.js
// Connects React dashboard to FastAPI + ntscraper backend

import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const POLL_INTERVAL = 5 * 60 * 1000; // 5 min — matches backend cache TTL

export function useAfconData() {
  const [tweets,  setTweets]  = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async (forceRefresh = false) => {
    try {
      const url = `${API_BASE}/api/tweets/afcon${forceRefresh ? "?force_refresh=true" : ""}`;
      const res = await fetch(url);

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const data = await res.json();
      setTweets(data.tweets ?? []);
      setMetrics(data.metrics ?? null);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(() => fetchData(), POLL_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [fetchData]);

  const analyzeSingle = useCallback(async (text) => {
    const res = await fetch(`${API_BASE}/api/analyze/single`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`Analyze error: HTTP ${res.status}`);
    return res.json();
  }, []);

  return {
    tweets,
    metrics,
    loading,
    error,
    lastUpdated,
    refresh: () => fetchData(true),
    analyzeSingle,
  };
}
