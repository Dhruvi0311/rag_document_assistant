"use client";

import React, { useEffect, useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useTheme } from 'next-themes';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoverNode, setHoverNode] = useState(null);
  
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const currentTheme = theme === "system" ? systemTheme : theme;
  const isDark = mounted && currentTheme === "dark";

  useEffect(() => {
    fetch('http://localhost:8000/api/graph')
      .then((res) => res.json())
      .then((data) => {
        setGraphData(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch graph data:", err);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isHovered = node === hoverNode;
    const label = node.id;
    const fontSize = node.group === 'file' ? 12 / globalScale : 10 / globalScale;
    
    // Draw glowing circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.val, 0, 2 * Math.PI, false);
    
    if (node.group === 'file') {
       ctx.fillStyle = '#3b82f6'; // Blue
       ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
       ctx.shadowBlur = (isHovered ? 20 : 10) * globalScale;
    } else {
       ctx.fillStyle = '#fb923c'; // Orange
       ctx.shadowColor = 'rgba(251, 146, 60, 0.8)';
       ctx.shadowBlur = (isHovered ? 15 : 5) * globalScale;
    }
    
    ctx.fill();
    ctx.shadowBlur = 0; // Reset shadow for text

    // Draw Text Labels
    // Only draw keyword labels if zoomed in, but always draw file labels
    if (globalScale > 1.2 || node.group === 'file' || isHovered) {
      ctx.font = `${isHovered ? 'bold' : 'normal'} ${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Text Background Pill
      const textWidth = ctx.measureText(label).width;
      const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.8);
      
      const yOffset = node.y + node.val + (fontSize * 1.5);
      
      ctx.fillStyle = isHovered 
        ? (isDark ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)') 
        : (isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.8)');
      
      ctx.beginPath();
      // Use standard arc methods to draw a rounded rect if roundRect isn't universally supported on canvas
      if (ctx.roundRect) {
        ctx.roundRect(node.x - bckgDimensions[0]/2, yOffset - bckgDimensions[1]/2, bckgDimensions[0], bckgDimensions[1], 4);
      } else {
        ctx.fillRect(node.x - bckgDimensions[0]/2, yOffset - bckgDimensions[1]/2, bckgDimensions[0], bckgDimensions[1]);
      }
      ctx.fill();
      
      // Text Shadow for readability
      if (isHovered) {
         ctx.shadowColor = 'rgba(0,0,0,0.3)';
         ctx.shadowBlur = 4;
      }
      
      ctx.fillStyle = node.group === 'file' 
        ? (isDark ? '#f8fafc' : '#1e293b') 
        : (isDark ? '#cbd5e1' : '#475569');
      ctx.fillText(label, node.x, yOffset);
      ctx.shadowBlur = 0;
      
      // Draw sub-metrics (chunk count or frequency) on hover
      if (isHovered) {
        const subText = node.group === 'file' ? `${node.chunk_count} semantic chunks` : `Frequency: ${node.frequency}`;
        const subFontSize = fontSize * 0.75;
        ctx.font = `italic ${subFontSize}px Sans-Serif`;
        ctx.fillStyle = isDark ? '#94a3b8' : '#64748b';
        ctx.fillText(subText, node.x, yOffset + bckgDimensions[1]);
      }
    }
  }, [hoverNode, isDark]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center w-full h-full bg-[#F4F7FB] dark:bg-slate-900 relative overflow-hidden transition-colors">
        <div className="absolute inset-0 geometric-pattern opacity-30 dark:opacity-10"></div>
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="font-sans text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Synthesizing Graph...</p>
        </div>
      </div>
    );
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center w-full h-full bg-[#F4F7FB] dark:bg-slate-900 transition-colors">
        <p className="text-slate-500 dark:text-slate-400 font-sans text-sm font-semibold">No indexed files available to generate the graph.</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full bg-gradient-to-br from-slate-50 to-[#F4F7FB] dark:from-slate-950 dark:to-slate-900 overflow-hidden relative transition-colors">
      
      {/* ── Glassmorphic Information Panel ── */}
      <div className="absolute top-6 left-6 z-10 bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl px-6 py-5 rounded-2xl border border-white/50 dark:border-slate-700/50 shadow-xl pointer-events-none transition-colors">
        <h3 className="font-sans text-lg font-black text-slate-800 dark:text-slate-100 tracking-tight">Intelligence Graph</h3>
        <p className="font-sans text-xs text-slate-500 dark:text-slate-400 mt-1.5 max-w-[220px] leading-relaxed">
          Watch how topics naturally emerge and cluster across your repository. Drag nodes to explore relationships.
        </p>
        
        <div className="flex flex-col gap-3 mt-5 pt-5 border-t border-slate-200/50 dark:border-slate-700/50">
          <div className="flex items-center gap-3">
            <span className="w-4 h-4 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)] inline-block"></span>
            <div>
              <p className="font-sans text-[11px] font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">File Node</p>
              <p className="font-sans text-[9px] text-slate-400 dark:text-slate-500">Size relative to chunk count</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-orange-400 shadow-[0_0_8px_rgba(251,146,60,0.6)] inline-block"></span>
            <div>
              <p className="font-sans text-[11px] font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">Keyword Node</p>
              <p className="font-sans text-[9px] text-slate-400 dark:text-slate-500">Size relative to cross-file frequency</p>
            </div>
          </div>
        </div>
      </div>

      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel={() => ""} // Disable default tooltip since we draw custom hover states
        nodeCanvasObject={drawNode}
        nodeCanvasObjectMode={() => "replace"}
        linkColor={() => isDark ? 'rgba(51, 65, 85, 0.8)' : 'rgba(203, 213, 225, 0.4)'}
        linkWidth={(link: any) => (link.source === hoverNode || link.target === hoverNode) ? 3 : 1}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={(link: any) => (link.source === hoverNode || link.target === hoverNode) ? 4 : 2}
        linkDirectionalParticleColor={() => isDark ? '#64748b' : '#94a3b8'}
        d3VelocityDecay={0.15}
        cooldownTicks={150}
        onNodeHover={(node) => setHoverNode(node)}
        onNodeDragEnd={(node: any) => {
          node.fx = node.x;
          node.fy = node.y;
        }}
      />
    </div>
  );
}
