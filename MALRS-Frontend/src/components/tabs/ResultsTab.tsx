import { motion } from "framer-motion";
import {
  Sparkles,
  FileSearch,
  AlertTriangle,
  TrendingUp,
  Download,
  RefreshCw,
  CheckCircle,
  BookOpen,
  Lightbulb,
  Terminal as TerminalIcon,
  FileCode,
  FileText,
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { GradientButton } from "@/components/ui/GradientButton";
import { AnalysisResult } from "@/hooks/useResearchState";
import { Terminal } from "@/components/Terminal";
import { ReportViewer } from "@/components/ReportViewer";
import { useState, useEffect } from "react";

interface ResultsTabProps {
  analysisResult: AnalysisResult | null;
  onReset: () => void;
  isAnalyzing: boolean;
}

export function ResultsTab({ analysisResult, onReset, isAnalyzing }: ResultsTabProps) {
  // Terminal visibility state with localStorage persistence
  const hasAnalysisCompleted = analysisResult !== null;
  const [isTerminalVisible, setIsTerminalVisible] = useState(() => {
    const saved = localStorage.getItem("terminal-visible");
    return saved === "true";
  });

  // Persist terminal visibility to localStorage
  useEffect(() => {
    localStorage.setItem("terminal-visible", String(isTerminalVisible));
  }, [isTerminalVisible]);

  if (!analysisResult) {
    return (
      <div className="space-y-6">
        <GlassCard className="text-center py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-muted/50 flex items-center justify-center">
              <FileSearch className="h-10 w-10 text-muted-foreground" />
            </div>
            <h3 className="heading-md text-foreground mb-2">No Analysis Yet</h3>
            <p className="body-md text-muted-foreground max-w-md mx-auto">
              Add your paper content in the Input & Configure tab and launch an
              analysis to see your novelty assessment results here.
            </p>
          </motion.div>
        </GlassCard>

        {/* Terminal Toggle Button */}
        <GlassCard>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Monitor analysis logs in real-time
            </p>
            <GradientButton
              variant={isTerminalVisible ? "primary" : "ghost"}
              size="sm"
              icon={<TerminalIcon className="h-4 w-4" />}
              onClick={() => setIsTerminalVisible(!isTerminalVisible)}
            >
              {isTerminalVisible ? "Hide" : "Show"} Terminal
            </GradientButton>
          </div>
        </GlassCard>

        {/* Terminal Component */}
        <Terminal 
          isVisible={isTerminalVisible} 
          onClose={() => setIsTerminalVisible(false)} 
        />

        {/* Agent Wise Analysis */}
        <ReportViewer
          title="Agent Wise Analysis"
          endpoint="/api/outputs/agent-analysis"
          isAnalyzing={isAnalyzing}
          hasAnalysisCompleted={hasAnalysisCompleted}
          type="text"
          icon={<FileCode className="h-5 w-5 text-secondary" />}
        />

        {/* Final Report */}
        <ReportViewer
          title="Final Report"
          endpoint="/api/outputs/final-report"
          isAnalyzing={isAnalyzing}
          hasAnalysisCompleted={hasAnalysisCompleted}
          type="markdown"
          icon={<FileText className="h-5 w-5 text-primary" />}
        />
      </div>
    );
  }

  const metrics = [
    {
      label: "Novelty Score",
      value: analysisResult.noveltyScore,
      suffix: "%",
      icon: Sparkles,
      color: "text-primary",
    },
    {
      label: "Related Papers",
      value: analysisResult.relatedPapers,
      icon: FileSearch,
      color: "text-secondary",
    },
    {
      label: "Key Gaps",
      value: analysisResult.keyGaps,
      icon: AlertTriangle,
      color: "text-accent",
    },
    {
      label: "Confidence",
      value: analysisResult.confidence,
      suffix: "%",
      icon: TrendingUp,
      color: "text-success",
    },
  ];

  const handleExport = async (format: string) => {
    try {
      // Prepare analysis data for export
      const exportData = {
        format: format,
        analysis_data: {
          research_idea: analysisResult.fullReport || '',
          domains: [],
          final_report: analysisResult.fullReport || '',
          papers: analysisResult.retrievedPapers || [],
          metrics: analysisResult.metrics || {},
          agent_outputs: analysisResult.agentOutputs || {}
        }
      };

      // Call export API
      const response = await fetch('http://localhost:5000/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData),
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Download the file
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Get filename from Content-Disposition header or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `research-report-${new Date().toISOString().split('T')[0]}.${format}`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
          >
            <GlassCard hover className="text-center">
              <div
                className={`w-12 h-12 mx-auto mb-3 rounded-full bg-muted/50 flex items-center justify-center`}
              >
                <metric.icon className={`h-6 w-6 ${metric.color}`} />
              </div>
              <motion.p
                className="text-3xl font-bold text-foreground"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
              >
                {metric.value}
                {metric.suffix}
              </motion.p>
              <p className="text-sm text-muted-foreground mt-1">
                {metric.label}
              </p>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Findings Card */}
      <GlassCard>
        <div className="space-y-6">
          {/* Novel Aspects */}
          <FindingSection
            title="Novel Aspects"
            icon={Sparkles}
            color="text-primary"
            items={analysisResult.novelAspects}
            type="bullet"
          />

          {/* Related Work */}
          <FindingSection
            title="Related Work"
            icon={BookOpen}
            color="text-secondary"
            items={analysisResult.relatedWork}
            type="numbered"
          />

          {/* Research Gaps */}
          <FindingSection
            title="Research Gaps"
            icon={AlertTriangle}
            color="text-accent"
            items={analysisResult.gaps}
            type="numbered"
          />

          {/* Recommendations */}
          <FindingSection
            title="Recommendations"
            icon={Lightbulb}
            color="text-success"
            items={analysisResult.recommendations}
            type="bullet"
          />
        </div>
      </GlassCard>

      {/* Export Panel */}
      <GlassCard>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap gap-3">
            <GradientButton
              variant="secondary"
              size="sm"
              icon={<Download className="h-4 w-4" />}
              onClick={() => handleExport("pdf")}
            >
              Export PDF
            </GradientButton>
            <GradientButton
              variant="secondary"
              size="sm"
              icon={<Download className="h-4 w-4" />}
              onClick={() => handleExport("tex")}
            >
              Export LaTeX
            </GradientButton>
            <GradientButton
              variant="secondary"
              size="sm"
              icon={<Download className="h-4 w-4" />}
              onClick={() => handleExport("md")}
            >
              Export Markdown
            </GradientButton>
          </div>
          <div className="flex gap-3">
            <GradientButton
              variant={isTerminalVisible ? "primary" : "ghost"}
              size="sm"
              icon={<TerminalIcon className="h-4 w-4" />}
              onClick={() => setIsTerminalVisible(!isTerminalVisible)}
            >
              {isTerminalVisible ? "Hide" : "Show"} Terminal
            </GradientButton>
            <GradientButton
              variant="ghost"
              size="sm"
              icon={<RefreshCw className="h-4 w-4" />}
              onClick={onReset}
            >
              Start New Analysis
            </GradientButton>
          </div>
        </div>
      </GlassCard>

      {/* Terminal Component */}
      <Terminal 
        isVisible={isTerminalVisible} 
        onClose={() => setIsTerminalVisible(false)} 
      />

      {/* Agent Wise Analysis */}
      <ReportViewer
        title="Agent Wise Analysis"
        endpoint="/api/outputs/agent-analysis"
        isAnalyzing={isAnalyzing}
        hasAnalysisCompleted={hasAnalysisCompleted}
        type="text"
        icon={<FileCode className="h-5 w-5 text-secondary" />}
      />

      {/* Final Report */}
      <ReportViewer
        title="Final Report"
        endpoint="/api/outputs/final-report"
        isAnalyzing={isAnalyzing}
        hasAnalysisCompleted={hasAnalysisCompleted}
        type="markdown"
        icon={<FileText className="h-5 w-5 text-primary" />}
      />
    </div>
  );
}

function FindingSection({
  title,
  icon: Icon,
  color,
  items,
  type,
}: {
  title: string;
  icon: React.ElementType;
  color: string;
  items: string[];
  type: "bullet" | "numbered";
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={`h-5 w-5 ${color}`} />
        <h4 className="font-semibold text-foreground">{title}</h4>
      </div>
      <ul className="space-y-2 pl-7">
        {items.map((item, index) => (
          <motion.li
            key={index}
            className="text-sm text-foreground/80 flex items-start gap-2"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            {type === "numbered" ? (
              <span className="text-muted-foreground font-medium min-w-[1.5rem]">
                {index + 1}.
              </span>
            ) : (
              <CheckCircle className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
            )}
            <span>{item}</span>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
