import React, { useState } from 'react';
import { AnalyticsData, CitationChunk } from '../types';

interface Props {
  analytics: AnalyticsData;
  topCitation?: CitationChunk;
}

export default function AnalyticsDashboard({ analytics, topCitation }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-4 border border-slate-200/60 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/80 rounded-xl overflow-hidden transition-all duration-300 w-full max-w-2xl shadow-sm">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-4 py-2.5 bg-white/50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-700 text-left transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="font-sans text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Retrieval Analytics</span>
        </div>
        <svg 
          className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} 
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="p-4 bg-white dark:bg-slate-800/80 border-t border-slate-100 dark:border-slate-700/50 grid grid-cols-2 sm:grid-cols-4 gap-4 animate-fade-in-up transition-colors">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Execution</span>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-black text-slate-700 dark:text-slate-100">{analytics.latency_ms}</span>
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">ms</span>
            </div>
          </div>
          
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Generation</span>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-black text-slate-700 dark:text-slate-100">{analytics.token_count}</span>
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">tokens</span>
            </div>
          </div>

          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Retrieval Pool</span>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-black text-slate-700 dark:text-slate-100">{analytics.dense_hits + analytics.sparse_hits}</span>
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">hits</span>
            </div>
          </div>

          {topCitation && topCitation.rank_shift !== undefined && (
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Rerank Shift</span>
              <div className="flex items-baseline gap-1">
                <span className={`text-lg font-black ${topCitation.rank_shift > 0 ? 'text-emerald-500' : topCitation.rank_shift < 0 ? 'text-red-500' : 'text-slate-700 dark:text-slate-100'}`}>
                  {topCitation.rank_shift > 0 ? '+' : ''}{topCitation.rank_shift}
                </span>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">pos</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
