import { useRef, useState, type DragEvent } from "react";
import { Upload } from "lucide-react";
import { useUpload } from "../hooks/useUpload";

const ACCEPTED = [".pptx", ".pdf"];
const ACCEPTED_MIME = ["application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/pdf"];

function isAccepted(file: File): boolean {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  return ACCEPTED.includes(ext) || ACCEPTED_MIME.includes(file.type);
}

export default function UploadPage() {
  const { upload, isUploading, error } = useUpload();
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!isAccepted(file)) {
      return;
    }
    upload(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => setDragOver(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-white tracking-tight">다듬</h1>
          <p className="mt-1 text-sm text-neutral-400">발표자료 디자인 일관성 분석</p>
        </div>

        <div
          className={[
            "border border-dashed rounded-lg p-10 flex flex-col items-center gap-4 cursor-pointer transition-colors duration-150",
            dragOver ? "border-amber-400 bg-[#1a1a1a]" : "border-neutral-700 bg-[#111111]",
            isUploading ? "pointer-events-none opacity-60" : "",
          ].join(" ")}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => !isUploading && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="파일 업로드 영역"
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && !isUploading) {
              inputRef.current?.click();
            }
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pptx,.pdf"
            className="hidden"
            onChange={onInputChange}
            disabled={isUploading}
          />

          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-6 h-6 border-2 border-neutral-600 border-t-amber-400 rounded-full animate-spin" />
              <p className="text-sm text-neutral-400">분석 준비 중...</p>
            </div>
          ) : (
            <>
              <Upload size={28} strokeWidth={1.5} className="text-neutral-500" />
              <div className="text-center">
                <p className="text-sm text-neutral-300">
                  파일을 드래그하거나 클릭하여 업로드
                </p>
                <p className="mt-1 text-xs text-neutral-500">.pptx, .pdf · 최대 50MB · 최대 50장</p>
              </div>
              <button
                type="button"
                className="rounded-md bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition-colors duration-150"
                onClick={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
              >
                파일 선택
              </button>
            </>
          )}
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-400 text-center">{error}</p>
        )}

        <p className="mt-4 text-xs text-neutral-600 text-center">
          업로드된 파일은 서버에 영구 저장되지 않습니다.
        </p>
      </div>
    </main>
  );
}
