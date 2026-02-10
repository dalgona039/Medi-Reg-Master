import { create } from "zustand";

interface QueryMetric {
  timestamp: Date;
  responseTime: number;
  contextSize: number;
  useDeepTraversal: boolean;
}

interface PerformanceState {
  // Metrics
  totalQueries: number;
  avgResponseTime: number;
  avgContextSize: number;
  deepTraversalUsage: number;
  queriesHistory: QueryMetric[];
  
  // Actions
  recordQuery: (metric: Omit<QueryMetric, "timestamp">) => void;
  resetMetrics: () => void;
}

const INITIAL_STATE = {
  totalQueries: 0,
  avgResponseTime: 0,
  avgContextSize: 0,
  deepTraversalUsage: 0,
  queriesHistory: [],
};

export const usePerformanceStore = create<PerformanceState>()((set, get) => ({
  ...INITIAL_STATE,
  
  recordQuery: (metric) => {
    set((state) => {
      const newQuery: QueryMetric = {
        ...metric,
        timestamp: new Date(),
      };
      
      const newHistory = [...state.queriesHistory, newQuery].slice(-50);
      const totalQueries = state.totalQueries + 1;
      
      // Calculate averages
      const avgResponseTime = 
        (state.avgResponseTime * state.totalQueries + metric.responseTime) / totalQueries;
      const avgContextSize = 
        (state.avgContextSize * state.totalQueries + metric.contextSize) / totalQueries;
      
      // Calculate deep traversal usage
      const deepTraversalCount = newHistory.filter(q => q.useDeepTraversal).length;
      const deepTraversalUsage = (deepTraversalCount / newHistory.length) * 100;
      
      return {
        totalQueries,
        avgResponseTime,
        avgContextSize,
        deepTraversalUsage,
        queriesHistory: newHistory,
      };
    });
  },
  
  resetMetrics: () => set(INITIAL_STATE),
}));
