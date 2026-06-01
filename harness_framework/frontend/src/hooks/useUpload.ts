import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadFile, startAnalysis } from "../services/api";
import type { UploadResponse } from "../types/api";

interface UseUploadReturn {
  upload: (file: File) => Promise<void>;
  isUploading: boolean;
  error: string | null;
  uploadResponse: UploadResponse | null;
}

export function useUpload(): UseUploadReturn {
  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);

  const upload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await uploadFile(file);
      setUploadResponse(uploaded);
      const { task_id } = await startAnalysis(uploaded.file_id);
      navigate(`/result/${task_id}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "업로드 중 오류가 발생했습니다. 다시 시도해주세요.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  return { upload, isUploading, error, uploadResponse };
}
