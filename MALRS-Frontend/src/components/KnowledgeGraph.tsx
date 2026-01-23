/**
 * Knowledge Graph Component
 * Interactive D3.js visualization of paper relationships
 */

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ZoomIn, ZoomOut, Maximize2, X } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';
import { GradientButton } from './ui/GradientButton';

interface Paper {
  handle: string;
  title: string;
  authors: string;
  year: string | number;
  abstract: string;
}

interface GraphNode {
  id: string;
  title: string;
  year: number;
  citations: number;
  domain: string;
}

interface GraphLink {
  source: string;
  target: string;
  type: 'citation' | 'similarity';
}

interface KnowledgeGraphProps {
  papers: Paper[];
  onNodeClick?: (paper: Paper) => void;
}

export function KnowledgeGraph({ papers, onNodeClick }: KnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (!svgRef.current || papers.length === 0) return;

    // Simple visualization using SVG (lightweight alternative to D3)
    renderSimpleGraph();
  }, [papers]);

  const renderSimpleGraph = () => {
    // Create nodes from papers
    const nodes: GraphNode[] = papers.map((paper, i) => ({
      id: paper.handle,
      title: paper.title,
      year: typeof paper.year === 'number' ? paper.year : parseInt(paper.year) || 2020,
      citations: Math.floor(Math.random() * 100), // Mock data
      domain: 'ML' // Mock data
    }));

    // Simple circular layout
    const width = 800;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    const svg = svgRef.current;
    if (!svg) return;

    // Clear previous content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Create links (simple connections between adjacent papers)
    nodes.forEach((node, i) => {
      if (i < nodes.length - 1) {
        const angle1 = (i / nodes.length) * 2 * Math.PI;
        const angle2 = ((i + 1) / nodes.length) * 2 * Math.PI;
        
        const x1 = centerX + radius * Math.cos(angle1);
        const y1 = centerY + radius * Math.sin(angle1);
        const x2 = centerX + radius * Math.cos(angle2);
        const y2 = centerY + radius * Math.sin(angle2);

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1.toString());
        line.setAttribute('y1', y1.toString());
        line.setAttribute('x2', x2.toString());
        line.setAttribute('y2', y2.toString());
        line.setAttribute('stroke', '#4a5568');
        line.setAttribute('stroke-width', '1');
        line.setAttribute('opacity', '0.3');
        svg.appendChild(line);
      }
    });

    // Create nodes
    nodes.forEach((node, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      // Node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', x.toString());
      circle.setAttribute('cy', y.toString());
      circle.setAttribute('r', '8');
      circle.setAttribute('fill', '#f59e0b');
      circle.setAttribute('stroke', '#fff');
      circle.setAttribute('stroke-width', '2');
      circle.setAttribute('cursor', 'pointer');
      circle.addEventListener('click', () => setSelectedNode(node));
      svg.appendChild(circle);

      // Node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', x.toString());
      text.setAttribute('y', (y - 15).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#e5e7eb');
      text.setAttribute('font-size', '10');
      text.textContent = node.id;
      svg.appendChild(text);
    });
  };

  if (papers.length === 0) {
    return (
      <GlassCard className="p-8 text-center">
        <p className="text-muted-foreground">No papers available for visualization</p>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={isFullscreen ? 'fixed inset-4 z-50' : ''}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-foreground">Knowledge Graph</h3>
        <div className="flex gap-2">
          <GradientButton
            size="sm"
            variant="ghost"
            icon={<ZoomIn className="h-4 w-4" />}
            onClick={() => {/* Zoom in */}}
          >
          </GradientButton>
          <GradientButton
            size="sm"
            variant="ghost"
            icon={<ZoomOut className="h-4 w-4" />}
            onClick={() => {/* Zoom out */}}
          >
          </GradientButton>
          <GradientButton
            size="sm"
            variant="ghost"
            icon={isFullscreen ? <X className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
          </GradientButton>
        </div>
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          width="100%"
          height={isFullscreen ? '80vh' : '400'}
          viewBox="0 0 800 600"
          className="bg-muted/20 rounded-lg"
        />

        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute top-4 right-4 glass-card p-4 max-w-xs"
          >
            <h4 className="font-semibold text-sm mb-2">{selectedNode.title}</h4>
            <p className="text-xs text-muted-foreground">Year: {selectedNode.year}</p>
            <p className="text-xs text-muted-foreground">Citations: {selectedNode.citations}</p>
            <GradientButton
              size="sm"
              className="mt-2 w-full"
              onClick={() => setSelectedNode(null)}
            >
              Close
            </GradientButton>
          </motion.div>
        )}
      </div>

      <div className="mt-4 flex gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-primary"></div>
          <span>Paper Node</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-muted-foreground"></div>
          <span>Citation Link</span>
        </div>
      </div>
    </GlassCard>
  );
}
