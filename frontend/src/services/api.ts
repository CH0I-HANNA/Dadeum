import axios from "axios";
import type { UploadResponse, AnalyzeResponse, TaskStatus, AnalysisResult } from "../types/api";

const BASE_URL = "http://localhost:8000";

const client = axios.create({ baseURL: BASE_URL });

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<UploadResponse>("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function startAnalysis(fileId: string): Promise<AnalyzeResponse> {
  const { data } = await client.post<AnalyzeResponse>(`/api/analyze/${fileId}`);
  return data;
}

export async function getResult(
  taskId: string
): Promise<TaskStatus & { result?: AnalysisResult }> {
  const { data } = await client.get<TaskStatus & { result?: AnalysisResult }>(
    `/api/result/${taskId}`
  );
  return data;
}

export function getThumbnailUrl(fileId: string, slideNum: number): string {
  return `${BASE_URL}/api/thumbnail/${fileId}/${slideNum}`;
}

export function getReportUrl(taskId: string): string {
  return `${BASE_URL}/api/report/${taskId}`;
}

export function getPreviewFixUrl(fileId: string, slideNum: number, taskId: string): string {
  return `${BASE_URL}/api/preview-fix/${fileId}/${slideNum}?task_id=${taskId}`;
}

export async function downloadFixedFile(fileId: string, taskId: string): Promise<void> {
  const response = await client.post(
    `/api/fix/${fileId}`,
    { task_id: taskId },
    { responseType: "blob" }
  );
  const url = URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = `dadeum-fixed-${fileId.slice(0, 8)}.pptx`;
  a.click();
  URL.revokeObjectURL(url);
}
