import { useEffect, useState, useCallback } from "react";
import { fetchStats, fetchHistory } from "../services/inspectionService";

export function useStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    fetchStats().then((data) => {
      setStats(data);
      setLoading(false);
    });
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { stats, loading, refresh };
}

export function useHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    fetchHistory().then((data) => {
      setHistory(data);
      setLoading(false);
    });
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { history, loading, refresh };
}
