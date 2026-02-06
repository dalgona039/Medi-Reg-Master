import { X, FileText, ExternalLink } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useEffect, useState } from "react";

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
  const [isSafari, setIsSafari] = useState(false);

  useEffect(() => {
    const ua = navigator.userAgent.toLowerCase();
    const isSafariBrowser = ua.includes('safari') && !ua.includes('chrome') && !ua.includes('chromium');
    setIsSafari(isSafariBrowser);
  }, []);

  if (!showPdfViewer || !pdfFile) return null;

  const pdfUrl = `${API_BASE_URL}/pdf/${encodeURIComponent(pdfFile)}`;
  const pdfUrlWithPage = `${pdfUrl}#page=${pdfPage}`;
  console.log('[PDF Viewer] Browser:', isSafari ? 'Safari' : 'Other');
  console.log('[PDF Viewer] Opening PDF:', pdfUrlWithPage);

  const handleOpenInNewTab = () => {
    window.open(pdfUrlWithPage, '_blank');
  };

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
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenInNewTab}
              className="p-2 hover:bg-indigo-100 text-indigo-600 rounded-lg transition-colors flex items-center gap-2"
              title="새 탭에서 열기"
            >
              <ExternalLink size={18} />
              <span className="text-sm">새 탭</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
              title="닫기"
            >
              <X size={20} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden bg-gray-100">
          {isSafari ? (
            <div className="flex flex-col items-center justify-center h-full p-8">
              <FileText size={64} className="text-indigo-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Safari에서는 PDF 페이지 이동이 제한됩니다
              </h3>
              <p className="text-gray-600 mb-6 text-center">
                정확한 페이지({pdfPage}페이지)로 이동하려면 새 탭에서 여세요.
              </p>
              <button
                onClick={handleOpenInNewTab}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <ExternalLink size={20} />
                새 탭에서 PDF 열기
              </button>
              <div className="mt-8 text-sm text-gray-500">
                또는 Chrome/Firefox 브라우저를 사용해주세요.
              </div>
            </div>
          ) : (
            <embed
              src={pdfUrlWithPage}
              type="application/pdf"
              className="w-full h-full"
            />
          )}
        </div>
      </div>
    </div>
  );
}
