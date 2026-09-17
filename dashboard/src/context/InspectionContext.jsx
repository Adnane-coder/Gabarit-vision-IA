import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { fetchCameraStatus, fetchAiStatus, runInspection } from "../services/inspectionService";

const InspectionContext = createContext(null);

export function InspectionProvider({ children }) {
  const [cameraStatus, setCameraStatus] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const refreshStatus = useCallback(async () => {
    try {
      const [camera, ai] = await Promise.all([fetchCameraStatus(), fetchAiStatus()]);
      setCameraStatus(camera);
      setAiStatus(ai);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    // System status (camera/AI availability) is polled; actual inspections
    // only run when the user explicitly triggers one — the real pipeline
    // works on a chosen tracé, not a continuous camera stream.
    const interval = setInterval(refreshStatus, 5000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  const launchInspection = useCallback(async (tracee) => {
    setRunning(true);
    setError(null);
    try {
      const result = await runInspection(tracee);
      setLastResult(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setRunning(false);
    }
  }, []);

  return (
    <InspectionContext.Provider
      value={{ cameraStatus, aiStatus, lastResult, running, error, launchInspection, refreshStatus }}
    >
      {children}
    </InspectionContext.Provider>
  );
}

export function useInspection() {
  const ctx = useContext(InspectionContext);
  if (!ctx) throw new Error("useInspection must be used within InspectionProvider");
  return ctx;
}
