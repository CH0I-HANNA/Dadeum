import { useQuery } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { getResult } from "../services/api";
import type { AnalysisResult, TaskStatus } from "../types/api";

const POLL_INTERVAL = 1500;
const CLIENT_TIMEOUT = 120_000;

interface UseAnalysisReturn {
  result: AnalysisResult | null;
  status: TaskStatus["status"];
  error: string | null;
  stage: string;
}

function getStage(elapsed: number, status: string): string {
  if (status === "completed" || status === "error") return "";
  if (elapsed < 5)  return "파일 파싱 중...";
  if (elapsed < 15) return "특징 추출 중...";
  if (elapsed < 30) return "이상 슬라이드 탐지 중...";
  return "결과 생성 중...";
}

export function useAnalysis(taskId: string): UseAnalysisReturn {
  const [timedOut, setTimedOut] = useState(false);
  // useRef를 사용하는 이유: 시작 시각은 한 번만 기록하면 되고,
  // 이 값이 바뀔 때 re-render가 불필요하기 때문이다.
  const startTimeRef = useRef<number | null>(null);
  const [stage, setStage] = useState("");

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
    startTimeRef.current = Date.now();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setTimedOut(true), CLIENT_TIMEOUT);
    return () => clearTimeout(timer);
  }, []);

  // stage는 React Query 폴링(1.5초마다)으로 data가 바뀔 때마다
  // startTimeRef.current와의 차이로 계산한다.
  // setStage는 setTimeout 콜백으로 감싸 effect 내 동기 setState 규칙을 준수한다.
  useEffect(() => {
    const status = data?.status ?? "pending";
    const start = startTimeRef.current;

    if (status === "completed" || status === "error" || timedOut) {
      const id = setTimeout(() => setStage(""), 0);
      return () => clearTimeout(id);
    }
    if (start === null) return;
    const elapsed = (Date.now() - start) / 1000;
    const computed = getStage(elapsed, status);
    const id = setTimeout(() => setStage(computed), 0);
    return () => clearTimeout(id);
  }, [data, timedOut]);

  if (timedOut && data?.status !== "completed") {
    return {
      result: null,
      status: "error",
      error: "분석 시간이 초과되었습니다. 슬라이드 수를 줄이거나 파일 크기를 줄여 다시 시도해주세요.",
      stage: "",
    };
  }

  return {
    result: data?.result ?? null,
    status: data?.status ?? "pending",
    error: data?.error_message ?? null,
    stage,
  };
}
