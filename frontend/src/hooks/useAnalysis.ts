import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { getResult } from "../services/api";
import type { AnalysisResult, TaskStatus } from "../types/api";

const POLL_INTERVAL = 1500;
const CLIENT_TIMEOUT = 120_000;

interface UseAnalysisReturn {
  result: AnalysisResult | null;
  status: TaskStatus["status"];
  error: string | null;
}

export function useAnalysis(taskId: string): UseAnalysisReturn {
  const [timedOut, setTimedOut] = useState(false);

  const { data } = useQuery({
    queryKey: ["result", taskId],
    queryFn: () => getResult(taskId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "error") return false;
      return POLL_INTERVAL;
    },
    enabled: !timedOut && taskId.length > 0,
  });

  useEffect(() => {
    const timer = setTimeout(() => setTimedOut(true), CLIENT_TIMEOUT);
    return () => clearTimeout(timer);
  }, []);

  if (timedOut && data?.status !== "completed") {
    return {
      result: null,
      status: "error",
      error: "분석 시간이 초과되었습니다. 슬라이드 수를 줄이거나 파일 크기를 줄여 다시 시도해주세요.",
    };
  }

  return {
    result: data?.result ?? null,
    status: data?.status ?? "pending",
    error: data?.error_message ?? null,
  };
}
