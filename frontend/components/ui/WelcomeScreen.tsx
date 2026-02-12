import { useState, useEffect } from "react";
import { FileText, FolderOpen } from "lucide-react";
import { api } from "@/lib/api";

interface WelcomeScreenProps {
  t: {
    welcomeTitle: string;
    welcomeDesc: string;
    shortcutKey: string;
    newSession: string;
    existingDocuments?: string;
    loadDocument?: string;
  };
  onLoadExistingIndex?: (indexFilename: string) => void;
}

export default function WelcomeScreen({ t, onLoadExistingIndex }: WelcomeScreenProps) {
  const [existingIndices, setExistingIndices] = useState<string[]>([]);

  useEffect(() => {
    const fetchIndices = async () => {
      try {
        const data = await api.listIndices();
        setExistingIndices(data.indices);
      } catch (error) {
        console.error("Failed to fetch existing indices:", error);
      }
    };
    fetchIndices();
  }, []);

  return (
    <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-80 pb-20">
      <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 shadow-xl">
        <FileText className="w-10 h-10 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-slate-700 mb-2">{t.welcomeTitle}</h2>
      <p className="max-w-md text-center text-slate-500">
        {t.welcomeDesc}
      </p>
      <p className="text-xs text-slate-400 mt-4">
        {t.shortcutKey}: <kbd className="px-2 py-1 bg-slate-100 rounded">Ctrl+K</kbd> {t.newSession}
      </p>

      {existingIndices.length > 0 && onLoadExistingIndex && (
        <div className="mt-10 w-full max-w-2xl">
          <div className="flex items-center gap-2 mb-4 text-slate-600">
            <FolderOpen size={18} />
            <h3 className="font-semibold">{t.existingDocuments || "기존 문서"}</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {existingIndices.map((indexFile) => {
              const docName = indexFile.replace('_index.json', '').split('_').slice(1).join(' ');
              return (
                <button
                  key={indexFile}
                  onClick={() => onLoadExistingIndex(indexFile)}
                  className="p-4 bg-white border border-slate-200 rounded-lg hover:border-indigo-400 hover:shadow-md transition-all text-left group"
                >
                  <div className="flex items-start gap-3">
                    <FileText size={20} className="text-indigo-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-700 group-hover:text-indigo-600 truncate">
                        {docName}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {t.loadDocument || "문서 열기"}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
