import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
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
      let message = "업로드 중 오류가 발생했습니다. 다시 시도해주세요.";
      if (axios.isAxiosError(err)) {
        const detail = err?.response?.data?.detail;
        if (detail) {
          message = detail;
        } else {
          const status = err.response?.status;
          if (status === 400) message = "파일 형식이 올바르지 않거나 손상된 파일입니다.";
          else if (status === 413) message = "파일 크기가 50MB를 초과합니다. 더 작은 파일을 사용해주세요.";
          else if (status === 503) message = "서버 저장 공간이 부족합니다. 잠시 후 다시 시도해주세요.";
        }
      }
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  return { upload, isUploading, error, uploadResponse };
}
