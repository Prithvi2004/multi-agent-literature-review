import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  FileText,
  Lightbulb,
  Layers,
  Play,
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { GradientButton } from "@/components/ui/GradientButton";
import { ProgressTracker } from "@/components/ProgressTracker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  PaperSection,
  SECTION_TYPES,
  RESEARCH_DOMAINS,
} from "@/hooks/useResearchState";
import { cn } from "@/lib/utils";

interface InputConfigureTabProps {
  paperSections: PaperSection[];
  researchIdea: string;
  selectedDomains: string[];
  uploadedFiles: { id: string; name: string; size: number; type: string }[];
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisStatus: string;
  completedSteps: string[];
  onAddSection: (type: string, content: string) => void;
  onRemoveSection: (id: string) => void;
  onSetResearchIdea: (idea: string) => void;
  onToggleDomain: (domain: string) => void;
  onRunAnalysis: () => void;
}

export function InputConfigureTab({
  paperSections,
  researchIdea,
  selectedDomains,
  uploadedFiles,
  isAnalyzing,
  analysisProgress,
  analysisStatus,
  completedSteps,
  onAddSection,
  onRemoveSection,
  onSetResearchIdea,
  onToggleDomain,
  onRunAnalysis,
}: InputConfigureTabProps) {
  const [sectionType, setSectionType] = useState<string>("");
  const [sectionContent, setSectionContent] = useState("");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set()
  );
  const [jsonPreviewOpen, setJsonPreviewOpen] = useState(false);
  const [customDomain, setCustomDomain] = useState("");

  const handleAddCustomDomain = () => {
    if (customDomain.trim()) {
      onToggleDomain(customDomain.trim());
      setCustomDomain("");
    }
  };

  const handleAddSection = () => {
    if (sectionType && sectionContent.trim()) {
      onAddSection(sectionType, sectionContent);
      setSectionType("");
      setSectionContent("");
    }
  };

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const canRunAnalysis = paperSections.length > 0 && !isAnalyzing;

  return (
    <div className="space-y-6">
      {/* Progress Tracker */}
      <ProgressTracker
        completedSteps={completedSteps}
        activeStep={paperSections.length === 0 ? "paper" : undefined}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Section Builder */}
        <div className="space-y-4">
          <GlassCard>
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-primary" />
              <h3 className="heading-md">Paper Section Builder</h3>
            </div>

            <div className="space-y-4">
              <Select value={sectionType} onValueChange={setSectionType}>
                <SelectTrigger className="bg-input border-border">
                  <SelectValue placeholder="Select section type..." />
                </SelectTrigger>
                <SelectContent>
                  {SECTION_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Textarea
                placeholder="Paste your section content here..."
                value={sectionContent}
                onChange={(e) => setSectionContent(e.target.value)}
                className="min-h-[150px] bg-input border-border resize-none"
              />

              <GradientButton
                onClick={handleAddSection}
                disabled={!sectionType || !sectionContent.trim()}
                icon={<Plus className="h-4 w-4" />}
                className="w-full"
              >
                Add Section
              </GradientButton>
            </div>
          </GlassCard>

          {/* Section List */}
          <AnimatePresence>
            {paperSections.map((section) => (
              <motion.div
                key={section.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <GlassCard className="p-0 overflow-hidden">
                  <Collapsible
                    open={expandedSections.has(section.id)}
                    onOpenChange={() => toggleSection(section.id)}
                  >
                    <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-3">
                        <Badge
                          variant="secondary"
                          className="bg-primary/10 text-primary"
                        >
                          {section.type}
                        </Badge>
                        <span className="text-sm text-muted-foreground truncate max-w-[200px]">
                          {section.content.slice(0, 50)}...
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <GradientButton
                          variant="danger"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRemoveSection(section.id);
                          }}
                          icon={<Trash2 className="h-3 w-3" />}
                        >
                          Remove
                        </GradientButton>
                        {expandedSections.has(section.id) ? (
                          <ChevronUp className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <div className="px-4 pb-4 border-t border-border/50 pt-4">
                        <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                          {section.content}
                        </p>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Right Column - Metrics & Options */}
        <div className="space-y-4">
          {/* Metrics Card */}
          <GlassCard>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                label="Sections Added"
                value={paperSections.length}
                icon={FileText}
              />
              <MetricCard
                label="Fields Selected"
                value={selectedDomains.length}
                icon={Layers}
              />
            </div>
          </GlassCard>

          {/* Research Idea */}
          <GlassCard>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="h-5 w-5 text-accent" />
              <h3 className="font-semibold text-foreground">
                Research Idea{" "}
                <span className="text-muted-foreground text-sm font-normal">
                  (Optional)
                </span>
              </h3>
            </div>
            <Textarea
              placeholder="Describe your research idea, e.g., 'Exploring neuro-symbolic AI approaches for automated scientific hypothesis generation using knowledge graphs and transformer architectures...'"
              value={researchIdea}
              onChange={(e) => onSetResearchIdea(e.target.value)}
              className="min-h-[120px] bg-input border-border resize-none"
            />
          </GlassCard>

          {/* Research Domains */}
          <GlassCard>
            <div className="flex items-center gap-2 mb-4">
              <Layers className="h-5 w-5 text-secondary" />
              <h3 className="font-semibold text-foreground">
                Research Domains{" "}
                <span className="text-muted-foreground text-sm font-normal">
                  (Optional)
                </span>
              </h3>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              {RESEARCH_DOMAINS.map((domain) => (
                <motion.button
                  key={domain}
                  onClick={() => onToggleDomain(domain)}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                    selectedDomains.includes(domain)
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                  whileTap={{ scale: 0.95 }}
                >
                  {domain}
                </motion.button>
              ))}
              {selectedDomains
                .filter((d) => !RESEARCH_DOMAINS.includes(d as any))
                .map((domain) => (
                  <motion.button
                    key={domain}
                    onClick={() => onToggleDomain(domain)}
                    className="px-3 py-1.5 rounded-full text-xs font-medium transition-all bg-primary text-primary-foreground flex items-center gap-1"
                    whileTap={{ scale: 0.95 }}
                  >
                    {domain}
                    <span className="opacity-70 text-[10px] ml-1">✕</span>
                  </motion.button>
                ))}
            </div>

            <div className="flex gap-2">
              <Input
                type="text"
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddCustomDomain()}
                placeholder="Add other domain..."
                className="flex-1"
              />
              <GradientButton
                onClick={handleAddCustomDomain}
                disabled={!customDomain.trim()}
                size="sm"
                icon={<Plus className="h-4 w-4" />}
              >
                Add
              </GradientButton>
            </div>
          </GlassCard>

          {/* JSON Preview */}
          <Collapsible open={jsonPreviewOpen} onOpenChange={setJsonPreviewOpen}>
            <GlassCard className="p-0">
              <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/30 transition-colors">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">
                    JSON Preview
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Sections: {paperSections.length} • Uploads:{" "}
                    {uploadedFiles.length}
                  </span>
                </div>
                {jsonPreviewOpen ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="px-4 pb-4 space-y-3 border-t border-border/50 pt-4">
                  <div className="glass-card p-3 rounded-md">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Paper Data
                    </p>
                    <pre className="text-xs text-foreground/80 overflow-auto font-mono">
                      {JSON.stringify(
                        {
                          sections: paperSections.map((s) => ({
                            type: s.type,
                            content: s.content.slice(0, 100) + "...",
                          })),
                          uploads: uploadedFiles.map((f) => f.name),
                        },
                        null,
                        2
                      )}
                    </pre>
                  </div>
                  <div className="glass-card p-3 rounded-md">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Optional Fields
                    </p>
                    <pre className="text-xs text-foreground/80 overflow-auto font-mono">
                      {JSON.stringify(
                        {
                          idea: researchIdea || null,
                          domains: selectedDomains,
                        },
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              </CollapsibleContent>
            </GlassCard>
          </Collapsible>
        </div>
      </div>

      {/* Analysis Progress / Launch Button */}
      <GlassCard>
        {isAnalyzing ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">
                {analysisStatus}
              </span>
              <span className="text-sm text-muted-foreground">
                {analysisProgress}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-primary to-secondary progress-glow"
                initial={{ width: 0 }}
                animate={{ width: `${analysisProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        ) : (
          <GradientButton
            onClick={onRunAnalysis}
            disabled={!canRunAnalysis}
            size="lg"
            icon={<Play className="h-5 w-5" />}
            className="w-full"
          >
            Launch Comprehensive Analysis
          </GradientButton>
        )}
      </GlassCard>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <div className="p-2 rounded-lg bg-primary/10">
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div>
        <motion.p
          className="text-2xl font-bold text-foreground"
          key={value}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          {value}
        </motion.p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
