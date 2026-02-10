import { create } from "zustand";
import type { TreeNode } from "@/lib/types";

interface UIState {
  // Sidebar
  isSidebarOpen: boolean;
  
  // Modals / Panels
  showSettings: boolean;
  showPerformance: boolean;
  showPdfViewer: boolean;
  showTree: boolean;
  
  // PDF Viewer state
  pdfFile: string | null;
  pdfPage: number;
  
  // Tree state
  selectedNode: TreeNode | null;
  expandedNodes: Set<string>;
  treeData: TreeNode | null;
  
  // Clipboard
  copiedId: string | null;
  
  // Actions - Sidebar
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  
  // Actions - Modals
  setShowSettings: (show: boolean) => void;
  setShowPerformance: (show: boolean) => void;
  setShowPdfViewer: (show: boolean) => void;
  setShowTree: (show: boolean) => void;
  
  // Actions - PDF Viewer
  openPdf: (file: string, page?: number) => void;
  closePdf: () => void;
  setPdfPage: (page: number) => void;
  
  // Actions - Tree
  setSelectedNode: (node: TreeNode | null) => void;
  setExpandedNodes: (nodes: Set<string>) => void;
  toggleNodeExpansion: (nodeId: string) => void;
  setTreeData: (data: TreeNode | null) => void;
  
  // Actions - Clipboard
  setCopiedId: (id: string | null) => void;
}

export const useUIStore = create<UIState>()((set, get) => ({
  // Initial state
  isSidebarOpen: true,
  showSettings: false,
  showPerformance: false,
  showPdfViewer: false,
  showTree: false,
  pdfFile: null,
  pdfPage: 1,
  selectedNode: null,
  expandedNodes: new Set<string>(),
  treeData: null,
  copiedId: null,
  
  // Sidebar actions
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  
  // Modal actions
  setShowSettings: (show) => set({ showSettings: show }),
  setShowPerformance: (show) => set({ showPerformance: show }),
  setShowPdfViewer: (show) => set({ showPdfViewer: show }),
  setShowTree: (show) => set({ showTree: show }),
  
  // PDF Viewer actions
  openPdf: (file, page = 1) => set({ 
    pdfFile: file, 
    pdfPage: page, 
    showPdfViewer: true 
  }),
  closePdf: () => set({ 
    showPdfViewer: false, 
    pdfFile: null 
  }),
  setPdfPage: (page) => set({ pdfPage: page }),
  
  // Tree actions
  setSelectedNode: (node) => set({ selectedNode: node }),
  setExpandedNodes: (nodes) => set({ expandedNodes: nodes }),
  toggleNodeExpansion: (nodeId) => set((state) => {
    const newExpanded = new Set(state.expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    return { expandedNodes: newExpanded };
  }),
  setTreeData: (data) => set({ treeData: data }),
  
  // Clipboard actions
  setCopiedId: (id) => set({ copiedId: id }),
}));
