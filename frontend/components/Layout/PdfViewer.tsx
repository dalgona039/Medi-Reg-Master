import { X, FileText } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface PdfViewerProps {
  showPdfViewer: boolean;
  pdfFile: string | null;
  pdfPage: number;
  onClose: () => void;
}

export default function PdfViewer({ 
  showPdfViewer, 
  pdfFile, 
  pdfPage,
  onClose 
}: PdfViewerProps) {
  if (!showPdfViewer || !pdfFile) return null;

  const pdfUrl = `${API_BASE_URL}/pdf/${encodeURIComponent(pdfFile)}#page=${pdfPage}`;
  console.log('[PDF Viewer] Opening PDF:', pdfUrl);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col">
        <div className="p-4 border-b flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <FileText size={20} className="text-indigo-600" />
            <h3 className="font-semibold text-slate-800">{pdfFile}</h3>
            <span className="text-sm text-slate-500">
              (페이지 {pdfPage})
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
            title="닫기"
          >
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-hidden bg-gray-100">
          <embed
            src={pdfUrl}
            type="application/pdf"
            className="w-full h-full"
          />
        </div>
      </div>
    </div>
  );
}
