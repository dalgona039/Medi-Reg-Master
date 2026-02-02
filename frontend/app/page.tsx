"use client";

import { useState, useRef, useEffect } from "react";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import { formatDistanceToNow } from "date-fns";
import { ko } from "date-fns/locale";
import { 
  Upload, FileText, Send, Bot, User, Loader2, 
  Plus, MessageSquare, PanelLeftClose, PanelLeft,
  Trash2, Copy, Check, ChevronRight, ChevronDown, FolderTree,
  Settings, X, Download, Search, Activity
} from "lucide-react";

type TreeNode = {
  id: string;
  title: string;
  summary?: string;
  page_ref?: string;
  children?: TreeNode[];
};

type TreeData = {
  document_name: string;
  tree: TreeNode;
};

type ComparisonResult = {
  has_comparison: boolean;
  documents_compared: string[];
  commonalities?: string;
  differences?: string;
};

type TraversalInfo = {
  used_deep_traversal: boolean;
  nodes_visited: string[];
  nodes_selected: Array<{
    document: string;
    title: string;
    page_ref: string;
  }>;
  max_depth: number;
  max_branches: number;
};

type ResolvedReference = {
  title: string;
  page_ref?: string;
  summary?: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  comparison?: ComparisonResult;
  traversal_info?: TraversalInfo;
  resolved_references?: ResolvedReference[];
};

type ChatSession = {
  id: string;
  title: string;
  indexFiles: string[];
  messages: Message[];
  createdAt: Date;
};

type ApiError = {
  detail: string;
};

const API_BASE_URL = "http://localhost:8000/api";
const STORAGE_KEY = "treerag-sessions";

// UI text translations
const UI_TEXT = {
  ko: {
    settings: "설정",
    export: "Export",
    treeStructure: "트리 구조",
    uploadPdf: "PDF 업로드 및 분석",
    uploading: "업로드 중...",
    indexing: "분석 중...",
    complete: "완료!",
    files: "파일",
    analysisSettings: "분석 설정",
    documentDomain: "문서 도메인",
    responseLanguage: "답변 언어",
    useDeepTraversal: "Deep Traversal 사용",
    maxDepth: "최대 깊이 (Max Depth)",
    maxBranches: "브랜치 수 (Max Branches)",
    deepTraversalDesc: "트리를 탐색하여 관련 섹션만 선택",
    flatModeDesc: "전체 문서를 사용 (레거시)",
    domainOptimized: "선택한 도메인에 최적화된 분석을 제공합니다",
    languageOptimized: "AI가 선택한 언어로 답변합니다",
    newChat: "새 대화",
    noHistory: "기록이 없습니다.",
    welcomeTitle: "TreeRAG",
    welcomeDesc: "PDF 문서를 업로드하면 AI가 자동으로 구조화하여 분석합니다.\\n계층적 트리 구조로 문서를 탐색하고 정확한 답변을 제공합니다.",
    shortcutKey: "단축키:",
    newSession: "새 세션",
    typeMessage: "메시지를 입력하세요...",
    sessionDeleted: "세션이 삭제되었습니다",
    analysisComplete: "분석이 완료되었습니다!",
    uploadFailed: "업로드/분석 실패",
    treeLoaded: "트리 로드 완료",
    treeLoadFailed: "트리 로드 실패",
    markdownSaved: "Markdown 파일로 저장되었습니다",
    nodeSelected: "노드 선택됨",
    pdfOpen: "PDF 열기",
    general: "일반 문서",
    medical: "의료/임상 문서",
    legal: "법률/계약 문서",
    financial: "금융/재무 문서",
    academic: "학술/연구 논문",
    korean: "한국어",
    english: "English",
    japanese: "日本語",
    deepTraversal: "Deep Traversal 사용",
    flatMode: "Flat Mode 사용",
    maxDepthDesc: "트리 탐색 최대 깊이 (1-10)",
    maxBranchesDesc: "레벨당 탐색할 자식 노드 수 (1-10)",
    tip: "팁",
    tipMessage: "깊이와 브랜치 수를 줄이면 응답 속도가 빨라지지만 정보가 제한될 수 있습니다.",
    analyzing: "AI가 규정을 분석하고 있습니다...",
    selectedSection: "선택된 섹션",
    sectionDeselected: "섹션 선택 해제됨",
    sectionQuestion: "섹션에 대해 질문하기...",
    send: "전송",
    disclaimer: "AI 답변은 업로드된 문서에 기반하지만, 중요한 결정 시 반드시 원문을 재확인하시기 바랍니다.",
    closeTree: "트리 닫기",
    tipTreeClick: "팁: Shift + 클릭으로 섹션 선택 후 질문하기",
    deleteSession: "세션 삭제",
    openSidebar: "사이드바 열기",
    closeSidebar: "사이드바 닫기",
    processing: "처리 중...",
    copiedToClipboard: "클립보드에 복사되었습니다",
    copyFailed: "복사 실패",
    recentHistory: "최근 기록",
    comparisonAnalysis: "문서 비교 분석",
    comparisonTarget: "비교 대상",
    commonalities: "공통점",
    differences: "차이점",
    crossReferenceResolved: "Cross-reference 해결됨",
    crossReferenceDesc: "질문에서 {count}개의 참조가 감지되어 자동으로 컨텍스트에 추가되었습니다",
    page: "페이지",
    searchPlaceholder: "대화 검색...",
    searchResults: "검색 결과",
    noSearchResults: "검색 결과가 없습니다",
    performance: "성능 모니터링",
    totalQueries: "총 질의 수",
    avgResponseTime: "평균 응답 시간",
    avgContextSize: "평균 컨텍스트 크기",
    deepTraversalUsage: "Deep Traversal 사용률",
    recentQueries: "최근 질의",
    tokens: "토큰",
    seconds: "초"
  },
  en: {
    settings: "Settings",
    export: "Export",
    treeStructure: "Tree View",
    uploadPdf: "Upload & Analyze PDF",
    uploading: "Uploading...",
    indexing: "Analyzing...",
    complete: "Complete!",
    files: "files",
    analysisSettings: "Analysis Settings",
    documentDomain: "Document Domain",
    responseLanguage: "Response Language",
    useDeepTraversal: "Use Deep Traversal",
    maxDepth: "Max Depth",
    maxBranches: "Max Branches",
    deepTraversalDesc: "Navigate tree to select relevant sections only",
    flatModeDesc: "Use entire document (legacy)",
    domainOptimized: "Provides analysis optimized for selected domain",
    languageOptimized: "AI responds in selected language",
    newChat: "New Chat",
    noHistory: "No history.",
    welcomeTitle: "TreeRAG",
    welcomeDesc: "Upload PDF documents and AI will automatically structure and analyze them.\\nExplore documents in hierarchical tree structure and get accurate answers.",
    shortcutKey: "Shortcut:",
    newSession: "New Session",
    typeMessage: "Type a message...",
    sessionDeleted: "Session deleted",
    analysisComplete: "Analysis completed!",
    uploadFailed: "Upload/Analysis failed",
    treeLoaded: "Tree loaded",
    treeLoadFailed: "Tree load failed",
    markdownSaved: "Saved as Markdown file",
    nodeSelected: "Node selected",
    pdfOpen: "Open PDF",
    general: "General Documents",
    medical: "Medical/Clinical",
    legal: "Legal/Contract",
    financial: "Financial/Accounting",
    academic: "Academic/Research",
    korean: "한국어 (Korean)",
    english: "English",
    japanese: "日本語 (Japanese)",
    deepTraversal: "Use Deep Traversal",
    flatMode: "Use Flat Mode",
    maxDepthDesc: "Maximum tree traversal depth (1-10)",
    maxBranchesDesc: "Number of child nodes to explore per level (1-10)",
    tip: "Tip",
    tipMessage: "Reducing depth and branches speeds up response but may limit information.",
    analyzing: "AI is analyzing the document...",
    selectedSection: "Selected Section",
    sectionDeselected: "Section deselected",
    sectionQuestion: "Ask about this section...",
    send: "Send",
    disclaimer: "AI responses are based on uploaded documents, but please verify important decisions with the original text.",
    closeTree: "Close tree",
    tipTreeClick: "Tip: Shift + Click to select section before asking",
    deleteSession: "Delete session",
    openSidebar: "Open sidebar",
    closeSidebar: "Close sidebar",
    processing: "Processing...",
    copiedToClipboard: "Copied to clipboard",
    copyFailed: "Copy failed",
    recentHistory: "Recent History",
    comparisonAnalysis: "Document Comparison Analysis",
    comparisonTarget: "Comparing",
    commonalities: "Commonalities",
    differences: "Differences",
    crossReferenceResolved: "Cross-references Resolved",
    crossReferenceDesc: "{count} references detected in question and automatically added to context",
    page: "Page",
    searchPlaceholder: "Search conversations...",
    searchResults: "Search Results",
    noSearchResults: "No results found",
    performance: "Performance Monitoring",
    totalQueries: "Total Queries",
    avgResponseTime: "Avg Response Time",
    avgContextSize: "Avg Context Size",
    deepTraversalUsage: "Deep Traversal Usage",
    recentQueries: "Recent Queries",
    tokens: "tokens",
    seconds: "sec"
  },
  ja: {
    settings: "設定",
    export: "エクスポート",
    treeStructure: "ツリー表示",
    uploadPdf: "PDF アップロード・分析",
    uploading: "アップロード中...",
    indexing: "分析中...",
    complete: "完了！",
    files: "ファイル",
    analysisSettings: "分析設定",
    documentDomain: "文書ドメイン",
    responseLanguage: "応答言語",
    useDeepTraversal: "Deep Traversal を使用",
    maxDepth: "最大深度",
    maxBranches: "ブランチ数",
    deepTraversalDesc: "ツリーを探索して関連セクションのみを選択",
    flatModeDesc: "文書全体を使用（レガシー）",
    domainOptimized: "選択したドメインに最適化された分析を提供",
    languageOptimized: "AIが選択した言語で応答します",
    newChat: "新しいチャット",
    noHistory: "履歴がありません。",
    welcomeTitle: "TreeRAG",
    welcomeDesc: "PDF文書をアップロードすると、AIが自動的に構造化して分析します。\\n階層的なツリー構造で文書を探索し、正確な回答を提供します。",
    shortcutKey: "ショートカット：",
    newSession: "新しいセッション",
    typeMessage: "メッセージを入力してください...",
    sessionDeleted: "セッションが削除されました",
    analysisComplete: "分析が完了しました！",
    uploadFailed: "アップロード/分析に失敗しました",
    treeLoaded: "ツリーをロードしました",
    treeLoadFailed: "ツリーのロードに失敗しました",
    markdownSaved: "Markdownファイルとして保存されました",
    nodeSelected: "ノードが選択されました",
    pdfOpen: "PDFを開く",
    general: "一般文書",
    medical: "医療/臨床",
    legal: "法律/契約",
    financial: "金融/財務",
    academic: "学術/研究",
    korean: "한국어 (韓国語)",
    english: "English (英語)",
    japanese: "日本語",
    deepTraversal: "Deep Traversal を使用",
    flatMode: "Flat Mode を使用",
    maxDepthDesc: "ツリー探索の最大深度 (1-10)",
    maxBranchesDesc: "レベルごとに探索する子ノード数 (1-10)",
    tip: "ヒント",
    tipMessage: "深度とブランチ数を減らすと応答速度が速くなりますが、情報が制限される場合があります。",
    analyzing: "AIが文書を分析しています...",
    selectedSection: "選択されたセクション",
    sectionDeselected: "セクション選択解除",
    sectionQuestion: "このセクションについて質問...",
    send: "送信",
    disclaimer: "AIの回答はアップロードされた文書に基づいていますが、重要な決定の際は必ず原文を再確認してください。",
    closeTree: "ツリーを閉じる",
    tipTreeClick: "ヒント: Shift + クリックでセクションを選択してから質問",
    deleteSession: "セッション削除",
    openSidebar: "サイドバーを開く",
    closeSidebar: "サイドバーを閉じる",
    processing: "処理中...",
    copiedToClipboard: "クリップボードにコピーされました",
    copyFailed: "コピー失敗",
    recentHistory: "最近の履歴",
    comparisonAnalysis: "文書比較分析",
    comparisonTarget: "比較対象",
    commonalities: "共通点",
    differences: "相違点",
    crossReferenceResolved: "クロスリファレンス解決済み",
    crossReferenceDesc: "質問から{count}個の参照が検出され、自動的にコンテキストに追加されました",
    page: "ページ",
    searchPlaceholder: "会話を検索...",
    searchResults: "検索結果",
    noSearchResults: "検索結果がありません",
    performance: "パフォーマンスモニタリング",
    totalQueries: "総質問数",
    avgResponseTime: "平均応答時間",
    avgContextSize: "平均コンテキストサイズ",
    deepTraversalUsage: "Deep Traversal 使用率",
    recentQueries: "最近の質問",
    tokens: "トークン",
    seconds: "秒"
  }
};

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showTree, setShowTree] = useState(false);
  const [treeData, setTreeData] = useState<TreeData | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [useDeepTraversal, setUseDeepTraversal] = useState(true);
  const [maxDepth, setMaxDepth] = useState(5);
  const [maxBranches, setMaxBranches] = useState(3);
  const [domainTemplate, setDomainTemplate] = useState("general");
  const [language, setLanguage] = useState("ko");
  const [showSettings, setShowSettings] = useState(false);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [pdfFile, setPdfFile] = useState<string | null>(null);
  const [pdfPage, setPdfPage] = useState(1);
  const [uploadProgress, setUploadProgress] = useState<{
    current: number;
    total: number;
    currentFile: string;
    status: 'idle' | 'uploading' | 'indexing' | 'complete';
  } | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showPerformance, setShowPerformance] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState<{
    totalQueries: number;
    avgResponseTime: number;
    avgContextSize: number;
    deepTraversalUsage: number;
    queriesHistory: Array<{
      timestamp: Date;
      responseTime: number;
      contextSize: number;
      useDeepTraversal: boolean;
    }>;
  }>({ totalQueries: 0, avgResponseTime: 0, avgContextSize: 0, deepTraversalUsage: 0, queriesHistory: [] });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get UI text based on selected language
  const t = UI_TEXT[language as keyof typeof UI_TEXT] || UI_TEXT.ko;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessions, currentSessionId]);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessions(parsed.map((s: ChatSession) => ({
          ...s,
          createdAt: new Date(s.createdAt)
        })));
      } catch (error) {
        console.error("Failed to load sessions:", error);
      }
    }
  }, []);

  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    }
  }, [sessions]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        createNewSession();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const currentMessages = currentSession?.messages || [];

  const createNewSession = () => {
    setCurrentSessionId(null);
    setInput("");
  };

  const deleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
    }
    toast.success(t.sessionDeleted);
  };

  const handleFileUploadAndIndex = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    const files = Array.from(e.target.files);
    const totalFiles = files.length;
    
    try {
      setIsUploading(true);

      const indexFiles: string[] = [];
      const docNames: string[] = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Upload phase
        setUploadProgress({
          current: i + 1,
          total: totalFiles,
          currentFile: file.name,
          status: 'uploading'
        });
        
        const formData = new FormData();
        formData.append("file", file);
        await axios.post(`${API_BASE_URL}/upload`, formData);

        // Indexing phase
        setUploadProgress({
          current: i + 1,
          total: totalFiles,
          currentFile: file.name,
          status: 'indexing'
        });
        
        const indexRes = await axios.post(`${API_BASE_URL}/index`, {
          filename: file.name,
        });
        
        indexFiles.push(indexRes.data.index_file);
        docNames.push(file.name.replace('.pdf', ''));
      }

      const sessionTitle = files.length === 1 
        ? docNames[0] 
        : `${docNames[0]} 외 ${files.length - 1}건`;

      const newSession: ChatSession = {
        id: Date.now().toString(),
        title: sessionTitle,
        indexFiles: indexFiles,
        messages: [{ 
          role: "assistant", 
          content: `반갑습니다! ${files.length}개 문서(${docNames.join(", ")})에 대한 분석 준비가 완료되었습니다. 무엇이든 물어보세요.` 
        }],
        createdAt: new Date(),
      };

      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      
      setUploadProgress({
        current: totalFiles,
        total: totalFiles,
        currentFile: '',
        status: 'complete'
      });
      
      setTimeout(() => setUploadProgress(null), 2000);
      toast.success(t.analysisComplete);
    } catch (error) {
      const err = error as { response?: { data?: ApiError } };
      const message = err.response?.data?.detail || t.uploadFailed;
      toast.error(message);
      console.error(error);
      setUploadProgress(null);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !currentSessionId || !currentSession) return;

    const userMsg = input;
    setInput("");

    const updatedMessages: Message[] = [
      ...currentSession.messages,
      { role: "user", content: userMsg }
    ];

    setSessions(prev => prev.map(session => 
      session.id === currentSessionId 
        ? { ...session, messages: updatedMessages }
        : session
    ));
    
    setIsGenerating(true);
    const startTime = Date.now();

    try {
      const requestBody: any = {
        question: userMsg,
        index_filenames: currentSession.indexFiles,
        use_deep_traversal: useDeepTraversal,
        max_depth: maxDepth,
        max_branches: maxBranches,
        domain_template: domainTemplate,
        language: language,
      };
      
      if (selectedNode) {
        requestBody.node_context = {
          id: selectedNode.id,
          title: selectedNode.title,
          page_ref: selectedNode.page_ref,
          summary: selectedNode.summary,
        };
      }
      
      const res = await axios.post(`${API_BASE_URL}/chat`, requestBody);
      
      const botMsg = res.data.answer;
      const citations = res.data.citations || [];
      const comparison = res.data.comparison || null;
      const traversalInfo = res.data.traversal_info || null;
      const resolvedReferences = res.data.resolved_references || null;

      const responseTime = (Date.now() - startTime) / 1000; // seconds
      const contextSize = traversalInfo?.total_tokens || 0;

      // Update performance metrics
      setPerformanceMetrics(prev => {
        const newHistory = [
          ...prev.queriesHistory,
          {
            timestamp: new Date(),
            responseTime,
            contextSize,
            useDeepTraversal
          }
        ].slice(-50); // Keep last 50 queries

        const totalQueries = prev.totalQueries + 1;
        const avgResponseTime = (prev.avgResponseTime * prev.totalQueries + responseTime) / totalQueries;
        const avgContextSize = (prev.avgContextSize * prev.totalQueries + contextSize) / totalQueries;
        const deepTraversalCount = newHistory.filter(q => q.useDeepTraversal).length;
        const deepTraversalUsage = (deepTraversalCount / newHistory.length) * 100;

        return {
          totalQueries,
          avgResponseTime,
          avgContextSize,
          deepTraversalUsage,
          queriesHistory: newHistory
        };
      });

      setSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { 
              ...session, 
              messages: [...updatedMessages, { 
                role: "assistant", 
                content: botMsg,
                citations,
                comparison,
                traversal_info: traversalInfo,
                resolved_references: resolvedReferences
              }] 
            }
          : session
      ));

    } catch (error) {
      const err = error as { response?: { data?: ApiError | { detail: any } } };
      let message = "응답 생성 실패";
      
      if (err.response?.data) {
        const data = err.response.data;
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
        } else {
          message = JSON.stringify(data.detail);
        }
      }
      
      setSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { 
              ...session, 
              messages: [...updatedMessages, { 
                role: "assistant", 
                content: `❌ 오류: ${message}` 
              }] 
            }
          : session
      ));
      
      toast.error(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const loadTreeStructure = async (indexFilename: string) => {
    try {
      const encodedFilename = encodeURIComponent(indexFilename);
      const res = await axios.get(`${API_BASE_URL}/tree/${encodedFilename}`);
      setTreeData(res.data);
      setShowTree(true);
      setExpandedNodes(new Set([res.data.tree.id]));
      toast.success(`${t.treeLoaded}: ${res.data.document_name}`);
    } catch (error) {
      toast.error(t.treeLoadFailed);
      console.error(error);
    }
  };

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const handleNodeClick = (node: TreeNode, hasChildren: boolean, e: React.MouseEvent) => {
    if (hasChildren) {
      toggleNode(node.id);
    }
    
    // Shift + 클릭으로 노드 선택 및 질문 생성
    if (e.shiftKey) {
      e.stopPropagation();
      setSelectedNode(node);
      
      const question = `"${node.title}" 섹션에 대해 자세히 설명해주세요.${node.page_ref ? ` (페이지 ${node.page_ref})` : ''}`;
      setInput(question);
      toast.success(`${t.nodeSelected}: ${node.title}`);
    }
  };

  const handleCitationClick = (citation: string) => {
    const match = citation.match(/(.+?),\s*p\.(\d+)/);
    if (match) {
      const [_, docName, pageNum] = match;
      const filename = `${docName.trim()}.pdf`;
      setPdfFile(filename);
      setPdfPage(parseInt(pageNum));
      setShowPdfViewer(true);
      toast.success(`${t.pdfOpen}: ${filename} (p.${pageNum})`);
    }
  };

  const exportToMarkdown = (session: ChatSession) => {
    let markdown = `# ${session.title}\n\n`;
    markdown += `**생성일:** ${session.createdAt.toLocaleString('ko-KR')}\n\n`;
    markdown += `**문서:** ${session.indexFiles.map(f => f.replace('_index.json', '')).join(', ')}\n\n`;
    markdown += `---\n\n`;

    session.messages.forEach((msg, idx) => {
      if (msg.role === 'user') {
        markdown += `## 질문 ${Math.floor((idx + 1) / 2)}\n\n`;
        markdown += `> ${msg.content}\n\n`;
      } else if (msg.role === 'assistant') {
        markdown += `### 답변\n\n`;
        markdown += `${msg.content}\n\n`;
        
        if (msg.citations && msg.citations.length > 0) {
          markdown += `**출처:**\n`;
          msg.citations.forEach(citation => {
            markdown += `- ${citation}\n`;
          });
          markdown += `\n`;
        }
        
        if (msg.resolved_references && msg.resolved_references.length > 0) {
          markdown += `**Cross-reference 해결됨:**\n`;
          msg.resolved_references.forEach(ref => {
            markdown += `- ${ref.title}`;
            if (ref.page_ref) markdown += ` (${ref.page_ref})`;
            markdown += `\n`;
          });
          markdown += `\n`;
        }
        
        if (msg.traversal_info && msg.traversal_info.used_deep_traversal) {
          markdown += `**Deep Traversal 통계:**\n`;
          markdown += `- Nodes Visited: ${msg.traversal_info.nodes_visited.length}\n`;
          markdown += `- Nodes Selected: ${msg.traversal_info.nodes_selected.length}\n`;
          markdown += `- Max Depth: ${msg.traversal_info.max_depth}\n`;
          markdown += `- Max Branches: ${msg.traversal_info.max_branches}\n\n`;
        }
        
        if (msg.comparison && msg.comparison.has_comparison) {
          markdown += `**문서 비교 분석**\n\n`;
          markdown += `비교 대상: ${msg.comparison.documents_compared.join(' ↔ ')}\n\n`;
          if (msg.comparison.commonalities) {
            markdown += `**공통점:**\n${msg.comparison.commonalities}\n\n`;
          }
          if (msg.comparison.differences) {
            markdown += `**차이점:**\n${msg.comparison.differences}\n\n`;
          }
        }
        
        markdown += `---\n\n`;
      }
    });

    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${session.title.replace(/[^a-zA-Z0-9가-힣\s]/g, '_')}_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success(t.markdownSaved);
  };

  const renderTreeNode = (node: TreeNode, level: number = 0): React.ReactElement => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = selectedNode?.id === node.id;
    
    return (
      <div key={node.id} className="mb-1">
        <div 
          className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
            level > 0 ? 'ml-' + (level * 4) : ''
          } ${
            isSelected ? 'bg-indigo-100 border border-indigo-300' : 'hover:bg-slate-50'
          }`}
          onClick={(e) => handleNodeClick(node, !!hasChildren, e)}
          title="클릭: 펼치기/접기 | Shift+클릭: 이 섹션 질문하기"
        >
          {hasChildren ? (
            isExpanded ? <ChevronDown size={16} className="mt-1 text-slate-600" /> : <ChevronRight size={16} className="mt-1 text-slate-600" />
          ) : (
            <div className="w-4" />
          )}
          <div className="flex-1 min-w-0">
            <div className={`font-medium text-sm ${
              isSelected ? 'text-indigo-800' : 'text-slate-800'
            }`}>{node.title}</div>
            {node.page_ref && (
              <div className="text-xs text-indigo-600 mt-0.5">📄 p.{node.page_ref}</div>
            )}
            {node.summary && isExpanded && (
              <div className="text-xs text-slate-600 mt-1 leading-relaxed">{node.summary}</div>
            )}
          </div>
        </div>
        {isExpanded && hasChildren && (
          <div className="ml-2">
            {node.children!.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success(t.copiedToClipboard);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      toast.error(t.copyFailed);
    }
  };

  return (
    <div className="flex h-screen bg-white font-sans text-slate-800 overflow-hidden">
      <Toaster position="top-center" />
      
      <aside 
        className={`${isSidebarOpen ? "w-72" : "w-0"} bg-[#f0f4f9] transition-all duration-300 flex flex-col border-r border-slate-200 overflow-hidden`}
      >
        <div className="p-4 flex items-center justify-between">
          <button 
            onClick={() => setIsSidebarOpen(false)}
            className="p-2 hover:bg-slate-200 rounded-full text-slate-500"
            aria-label={t.closeSidebar}
          >
            <PanelLeftClose size={20} />
          </button>
        </div>

        <div className="px-4 mb-6">
          <button 
            onClick={createNewSession}
            className="flex items-center gap-3 bg-[#dde3ea] hover:bg-[#d0dbe7] text-slate-700 px-4 py-3 rounded-xl w-full transition-colors font-medium text-sm"
            title={`${t.newChat} (Ctrl+K)`}
          >
            <Plus size={18} />
            {t.newChat}
          </button>
        </div>

        <div className="px-4 mb-4">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t.searchPlaceholder}
              className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2">
          <div className="text-xs font-semibold text-slate-500 px-4 mb-2">
            {searchQuery ? t.searchResults : t.recentHistory}
          </div>
          {sessions.filter(session => {
            if (!searchQuery.trim()) return true;
            const query = searchQuery.toLowerCase();
            // 제목 검색
            if (session.title.toLowerCase().includes(query)) return true;
            // 대화 내용 검색
            return session.messages.some(msg => 
              msg.content.toLowerCase().includes(query)
            );
          }).map((session) => (
            <div
              key={session.id}
              className={`group relative w-full text-left flex items-center gap-3 px-4 py-2 rounded-full text-sm mb-1 transition-colors ${
                currentSessionId === session.id 
                  ? "bg-[#c4d7ed] text-slate-900 font-medium" 
                  : "hover:bg-[#e0e5eb] text-slate-600"
              }`}
            >
              <button
                onClick={() => setCurrentSessionId(session.id)}
                className="flex items-center gap-3 flex-1 min-w-0"
              >
                <MessageSquare size={16} className="flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="truncate">{session.title}</div>
                  <div className="text-xs text-slate-400">
                    {formatDistanceToNow(session.createdAt, { addSuffix: true, locale: ko })}
                  </div>
                </div>
              </button>
              <button
                onClick={(e) => deleteSession(session.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded-full transition-opacity"
                aria-label={t.deleteSession}
              >
                <Trash2 size={14} className="text-red-600" />
              </button>
            </div>
          ))}
          
          {sessions.length === 0 && (
            <div className="text-center text-slate-400 text-xs mt-10">
              {t.noHistory}
            </div>
          )}
          
          {sessions.length > 0 && searchQuery && sessions.filter(session => {
            const query = searchQuery.toLowerCase();
            if (session.title.toLowerCase().includes(query)) return true;
            return session.messages.some(msg => msg.content.toLowerCase().includes(query));
          }).length === 0 && (
            <div className="text-center text-slate-400 text-xs mt-10">
              {t.noSearchResults}
            </div>
          )}
        </div>
      </aside>

      <main className="flex-1 flex flex-col h-full relative">
        
        <header className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-white z-10">
          <div className="flex items-center gap-2">
            {!isSidebarOpen && (
              <button 
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 hover:bg-slate-100 rounded-full text-slate-500 mr-2"
                aria-label={t.openSidebar}
              >
                <PanelLeft size={20} />
              </button>
            )}
            <h1 className="text-lg font-semibold text-slate-700 flex items-center gap-2">
              TreeRAG <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">AI</span>
            </h1>
          </div>

          {!currentSessionId && (
            <div className="flex items-center gap-3">
              <label className="cursor-pointer flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors">
                {isUploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
                {isUploading ? t.processing : t.uploadPdf}
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept=".pdf"
                  multiple
                  className="hidden" 
                  onChange={handleFileUploadAndIndex}
                  disabled={isUploading}
                />
              </label>
            </div>
          )}

          <div className="flex items-center gap-2">
            {/* Performance button - always visible */}
            <button
              onClick={() => setShowPerformance(!showPerformance)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 text-sm rounded-lg transition-colors"
              title={t.performance}
            >
              <Activity size={16} />
              {t.performance}
            </button>

            {/* Settings button - always visible */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-lg transition-colors"
              title={t.settings}
            >
              <Settings size={16} />
              {t.settings}
            </button>
            
            {/* Export and Tree buttons - only when session exists */}
            {currentSessionId && currentSession && (
              <>
                <button
                  onClick={() => exportToMarkdown(currentSession)}
                  className="flex items-center gap-2 px-4 py-2 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 text-sm rounded-lg transition-colors"
                  title={t.export}
                >
                  <Download size={16} />
                  {t.export}
                </button>
                <button
                  onClick={() => loadTreeStructure(currentSession.indexFiles[0])}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-lg transition-colors"
                  title={t.treeStructure}
                >
                  <FolderTree size={16} />
                  {t.treeStructure}
                </button>
              </>
            )}
          </div>
        </header>

        {uploadProgress && (
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-200 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Loader2 className="animate-spin text-emerald-600" size={16} />
                  <span className="text-sm font-semibold text-slate-800">
                    {uploadProgress.status === 'uploading' && t.uploading}
                    {uploadProgress.status === 'indexing' && t.indexing}
                    {uploadProgress.status === 'complete' && t.complete}
                  </span>
                </div>
                <span className="text-xs text-slate-600">
                  {uploadProgress.current} / {uploadProgress.total} {t.files}
                </span>
              </div>
              <div className="bg-white rounded-full h-2 overflow-hidden mb-2">
                <div 
                  className="bg-gradient-to-r from-emerald-500 to-green-500 h-full transition-all duration-300"
                  style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                />
              </div>
              {uploadProgress.currentFile && (
                <p className="text-xs text-slate-600 truncate">
                  📄 {uploadProgress.currentFile}
                </p>
              )}
            </div>
          </div>
        )}

        {showPerformance && (
          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-blue-200 p-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <Activity size={16} className="text-blue-600" />
                {t.performance}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <div className="text-xs text-slate-500 mb-1">{t.totalQueries}</div>
                  <div className="text-2xl font-bold text-blue-600">{performanceMetrics.totalQueries}</div>
                </div>
                
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <div className="text-xs text-slate-500 mb-1">{t.avgResponseTime}</div>
                  <div className="text-2xl font-bold text-green-600">
                    {performanceMetrics.avgResponseTime.toFixed(2)}{t.seconds}
                  </div>
                </div>
                
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <div className="text-xs text-slate-500 mb-1">{t.avgContextSize}</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.round(performanceMetrics.avgContextSize).toLocaleString()} {t.tokens}
                  </div>
                </div>
                
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <div className="text-xs text-slate-500 mb-1">{t.deepTraversalUsage}</div>
                  <div className="text-2xl font-bold text-indigo-600">
                    {performanceMetrics.deepTraversalUsage.toFixed(0)}%
                  </div>
                </div>
              </div>
              
              {performanceMetrics.queriesHistory.length > 0 && (
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <div className="text-xs font-medium text-slate-700 mb-2">{t.recentQueries}</div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {performanceMetrics.queriesHistory.slice(-10).reverse().map((query, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-slate-600">
                          {new Date(query.timestamp).toLocaleTimeString()}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-green-600">{query.responseTime.toFixed(2)}{t.seconds}</span>
                          <span className="text-purple-600">{query.contextSize.toLocaleString()} {t.tokens}</span>
                          {query.useDeepTraversal && (
                            <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded text-xs">Deep</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {showSettings && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-200 p-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <Settings size={16} className="text-indigo-600" />
                {t.analysisSettings}
              </h3>
              
              {/* Domain Template Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  📋 {t.documentDomain}
                </label>
                <select
                  value={domainTemplate}
                  onChange={(e) => setDomainTemplate(e.target.value)}
                  className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="general">📋 {t.general}</option>
                  <option value="medical">🏥 {t.medical}</option>
                  <option value="legal">⚖️ {t.legal}</option>
                  <option value="financial">💼 {t.financial}</option>
                  <option value="academic">🎓 {t.academic}</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  {t.domainOptimized}
                </p>
              </div>
              
              {/* Language Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  🌐 {t.responseLanguage}
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="ko">🇰🇷 {t.korean}</option>
                  <option value="en">🇺🇸 {t.english}</option>
                  <option value="ja">🇯🇵 {t.japanese}</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  {t.languageOptimized}
                </p>
              </div>
              
              {/* Deep Traversal Settings */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useDeepTraversal}
                      onChange={(e) => setUseDeepTraversal(e.target.checked)}
                      className="w-4 h-4 text-indigo-600 rounded"
                    />
                    <span className="text-sm font-medium text-slate-700">{t.deepTraversal}</span>
                  </label>
                  <p className="text-xs text-slate-500 mt-1 ml-6">
                    {useDeepTraversal ? t.deepTraversalDesc : t.flatModeDesc}
                  </p>
                </div>

                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {t.maxDepth}
                  </label>
                  <input
                    type="number"
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(Number(e.target.value))}
                    min="1"
                    max="10"
                    disabled={!useDeepTraversal}
                    className="w-full px-3 py-1 border border-slate-300 rounded text-sm disabled:bg-slate-100 disabled:text-slate-400"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    {t.maxDepthDesc}
                  </p>
                </div>

                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {t.maxBranches}
                  </label>
                  <input
                    type="number"
                    value={maxBranches}
                    onChange={(e) => setMaxBranches(Number(e.target.value))}
                    min="1"
                    max="10"
                    disabled={!useDeepTraversal}
                    className="w-full px-3 py-1 border border-slate-300 rounded text-sm disabled:bg-slate-100 disabled:text-slate-400"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    {t.maxBranchesDesc}
                  </p>
                </div>
              </div>
              <div className="mt-3 text-xs text-blue-700 bg-blue-100 p-2 rounded">
                💡 <strong>{t.tip}:</strong> {t.tipMessage}
              </div>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth bg-white">
          {!currentSessionId ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-80 pb-20">
              <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 shadow-xl">
                <FileText className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-slate-700 mb-2">TreeRAG</h2>
              <p className="max-w-md text-center text-slate-500">
                {t.welcomeDesc}
              </p>
              <p className="text-xs text-slate-400 mt-4">
                {t.shortcutKey}: <kbd className="px-2 py-1 bg-slate-100 rounded">Ctrl+K</kbd> {t.newSession}
              </p>
            </div>
          ) : (
            currentMessages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 max-w-4xl mx-auto ${msg.role === 'user' ? 'justify-end' : ''}`}>
                
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot size={18} className="text-indigo-600" />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div 
                    className={`group relative px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                      msg.role === 'user' 
                        ? "bg-[#e7effe] text-slate-800 rounded-br-none ml-auto max-w-[80%]" 
                        : "bg-white border border-slate-100 text-slate-800 rounded-tl-none"
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    
                    <button
                      onClick={() => copyToClipboard(msg.content, `${idx}`)}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 bg-slate-100 hover:bg-slate-200 rounded transition-opacity"
                      aria-label="복사"
                    >
                      {copiedId === `${idx}` ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                  </div>
                  
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2 ml-1">
                      {msg.citations.map((citation, i) => (
                        <button
                          key={i}
                          onClick={() => handleCitationClick(citation)}
                          className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded-full border border-indigo-100 hover:bg-indigo-100 cursor-pointer transition-colors"
                        >
                          📎 {citation}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {msg.comparison && msg.comparison.has_comparison && (
                    <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                          <span className="text-lg">📊</span>
                        </div>
                        <h4 className="font-semibold text-amber-900">{t.comparisonAnalysis}</h4>
                      </div>
                      
                      <div className="text-sm text-amber-800 mb-2">
                        <strong>{t.comparisonTarget}:</strong> {msg.comparison.documents_compared.join(" ↔ ")}
                      </div>
                      
                      {msg.comparison.commonalities && (
                        <div className="mb-3">
                          <div className="font-medium text-green-700 mb-1">✓ {t.commonalities}</div>
                          <div className="text-sm text-gray-700 bg-white p-2 rounded">
                            {msg.comparison.commonalities}
                          </div>
                        </div>
                      )}
                      
                      {msg.comparison.differences && (
                        <div>
                          <div className="font-medium text-red-700 mb-1">⚠ {t.differences}</div>
                          <div className="text-sm text-gray-700 bg-white p-2 rounded overflow-x-auto">
                            <ReactMarkdown>{msg.comparison.differences}</ReactMarkdown>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {msg.resolved_references && msg.resolved_references.length > 0 && (
                    <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-xl">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                          <span className="text-lg">🔗</span>
                        </div>
                        <h4 className="font-semibold text-purple-900">{t.crossReferenceResolved}</h4>
                      </div>
                      <div className="text-xs text-purple-700 mb-2">
                        {t.crossReferenceDesc.replace('{count}', msg.resolved_references.length.toString())}
                      </div>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {msg.resolved_references.map((ref, i) => (
                          <div key={i} className="bg-white p-2 rounded text-sm">
                            <div className="font-medium text-purple-700">{ref.title}</div>
                            {ref.page_ref && (
                              <div className="text-xs text-slate-500 mt-1">{t.page}: {ref.page_ref}</div>
                            )}
                            {ref.summary && (
                              <div className="text-xs text-slate-600 mt-1 line-clamp-2">{ref.summary}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.traversal_info && msg.traversal_info.used_deep_traversal && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-lg">🌲</span>
                        </div>
                        <h4 className="font-semibold text-blue-900">Deep Traversal 정보</h4>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                        <div className="bg-white p-2 rounded">
                          <span className="text-blue-600 font-medium">탐색한 노드:</span>
                          <span className="ml-2 text-slate-700">{msg.traversal_info.nodes_visited.length}개</span>
                        </div>
                        <div className="bg-white p-2 rounded">
                          <span className="text-blue-600 font-medium">선택된 노드:</span>
                          <span className="ml-2 text-slate-700">{msg.traversal_info.nodes_selected.length}개</span>
                        </div>
                        <div className="bg-white p-2 rounded">
                          <span className="text-blue-600 font-medium">최대 깊이:</span>
                          <span className="ml-2 text-slate-700">{msg.traversal_info.max_depth}</span>
                        </div>
                        <div className="bg-white p-2 rounded">
                          <span className="text-blue-600 font-medium">브랜치 수:</span>
                          <span className="ml-2 text-slate-700">{msg.traversal_info.max_branches}</span>
                        </div>
                      </div>

                      {msg.traversal_info.nodes_selected.length > 0 && (
                        <div>
                          <div className="font-medium text-blue-700 mb-2 text-sm">선택된 섹션:</div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {msg.traversal_info.nodes_selected.map((node, i) => (
                              <div key={i} className="text-xs bg-white p-2 rounded flex items-start gap-2">
                                <span className="text-blue-500 flex-shrink-0">•</span>
                                <div className="flex-1 min-w-0">
                                  <span className="font-medium text-slate-700">{node.title}</span>
                                  <span className="text-slate-500 ml-2">
                                    ({node.document}, p.{node.page_ref})
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0 mt-1">
                    <User size={18} className="text-slate-600" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {isGenerating && (
            <div className="flex gap-4 max-w-4xl mx-auto">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                <Loader2 size={18} className="animate-spin text-indigo-600" />
              </div>
              <div className="px-5 py-3 bg-white text-slate-500 text-sm">
                {t.analyzing}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {currentSessionId && (
          <div className="bg-white p-4 md:pb-6 border-t border-slate-100">
            {selectedNode && (
              <div className="max-w-3xl mx-auto mb-3 flex items-center gap-2 text-xs bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-200">
                <span className="text-indigo-700">📌 {t.selectedSection}:</span>
                <span className="font-medium text-indigo-900">{selectedNode.title}</span>
                {selectedNode.page_ref && (
                  <span className="text-indigo-600">(p.{selectedNode.page_ref})</span>
                )}
                <button
                  onClick={() => {
                    setSelectedNode(null);
                    toast.success(t.sectionDeselected);
                  }}
                  className="ml-auto text-indigo-600 hover:text-indigo-800"
                  aria-label={t.sectionDeselected}
                >
                  ✕
                </button>
              </div>
            )}
            <div className="max-w-3xl mx-auto relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isGenerating && handleSendMessage()}
                placeholder={selectedNode ? `"${selectedNode.title}" ${t.sectionQuestion}` : t.typeMessage}
                disabled={isGenerating}
                className="w-full bg-[#f0f4f9] hover:bg-[#e9eef6] focus:bg-white border-2 border-transparent focus:border-indigo-200 rounded-full pl-6 pr-14 py-4 text-slate-700 placeholder:text-slate-400 focus:outline-none transition-all shadow-sm"
                aria-label={t.typeMessage}
              />
              <button 
                onClick={handleSendMessage}
                disabled={!input.trim() || isGenerating}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                aria-label={t.send}
              >
                <Send size={18} />
              </button>
            </div>
            <div className="text-center mt-2 text-xs text-slate-400">
              {t.disclaimer}
            </div>
          </div>
        )}

      </main>

      {showTree && treeData && (
        <aside className="w-96 bg-white border-l border-slate-200 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderTree size={18} className="text-indigo-600" />
              <h3 className="font-semibold text-slate-800">{t.treeStructure}</h3>
            </div>
            <button
              onClick={() => {
                setShowTree(false);
                setSelectedNode(null);
              }}
              className="p-1 hover:bg-slate-100 rounded"
              aria-label={t.closeTree}
            >
              <PanelLeft size={18} className="text-slate-500" />
            </button>
          </div>
          
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-100">
            <div className="text-sm font-medium text-slate-700 mb-1">{treeData.document_name}</div>
            <div className="text-xs text-slate-500">
              💡 {t.tipTreeClick}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {renderTreeNode(treeData.tree)}
          </div>
        </aside>
      )}

      {showPdfViewer && pdfFile && (
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
                onClick={() => setShowPdfViewer(false)}
                className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
                title="닫기"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <iframe
                src={`${API_BASE_URL}/pdf/${pdfFile}#page=${pdfPage}`}
                className="w-full h-full border-0"
                title="PDF Viewer"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}