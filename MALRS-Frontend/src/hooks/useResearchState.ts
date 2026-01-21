import { useState, useCallback } from "react";

export interface PaperSection {
  id: string;
  type: string;
  content: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
}

export interface AnalysisResult {
  noveltyScore: number;
  relatedPapers: number;
  keyGaps: number;
  confidence: number;
  novelAspects: string[];
  relatedWork: string[];
  gaps: string[];
  recommendations: string[];
}

export interface ResearchState {
  paperSections: PaperSection[];
  researchIdea: string;
  selectedDomains: string[];
  uploadedFiles: UploadedFile[];
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisStatus: string;
}

const initialState: ResearchState = {
  paperSections: [],
  researchIdea: "",
  selectedDomains: [],
  uploadedFiles: [],
  analysisResult: null,
  isAnalyzing: false,
  analysisProgress: 0,
  analysisStatus: "",
};

export const SECTION_TYPES = [
  "Abstract",
  "Introduction",
  "Literature Review",
  "Methodology",
  "Results",
  "Discussion",
  "Conclusion",
  "References",
] as const;

export const RESEARCH_DOMAINS = [
  "Machine Learning",
  "Natural Language Processing",
  "Computer Vision",
  "Robotics",
  "Bioinformatics",
  "Quantum Computing",
  "Cybersecurity",
  "Data Science",
  "Human-Computer Interaction",
  "Distributed Systems",
  "Software Engineering",
  "Information Retrieval",
  "Knowledge Graphs",
  "Reinforcement Learning",
  "Neural Networks",
] as const;

export function useResearchState() {
  const [state, setState] = useState<ResearchState>(initialState);

  const addSection = useCallback((type: string, content: string) => {
    const newSection: PaperSection = {
      id: crypto.randomUUID(),
      type,
      content,
    };
    setState((prev) => ({
      ...prev,
      paperSections: [...prev.paperSections, newSection],
    }));
  }, []);

  const removeSection = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      paperSections: prev.paperSections.filter((s) => s.id !== id),
    }));
  }, []);

  const setResearchIdea = useCallback((idea: string) => {
    setState((prev) => ({ ...prev, researchIdea: idea }));
  }, []);

  const toggleDomain = useCallback((domain: string) => {
    setState((prev) => ({
      ...prev,
      selectedDomains: prev.selectedDomains.includes(domain)
        ? prev.selectedDomains.filter((d) => d !== domain)
        : [...prev.selectedDomains, domain],
    }));
  }, []);

  const addFile = useCallback((file: File) => {
    const uploadedFile: UploadedFile = {
      id: crypto.randomUUID(),
      name: file.name,
      size: file.size,
      type: file.type,
    };
    setState((prev) => ({
      ...prev,
      uploadedFiles: [...prev.uploadedFiles, uploadedFile],
    }));
  }, []);

  const removeFile = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      uploadedFiles: prev.uploadedFiles.filter((f) => f.id !== id),
    }));
  }, []);

  const clearFiles = useCallback(() => {
    setState((prev) => ({ ...prev, uploadedFiles: [] }));
  }, []);

  const runAnalysis = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      isAnalyzing: true,
      analysisProgress: 0,
      analysisStatus: "Initializing analysis...",
    }));

    const stages = [
      { progress: 20, status: "Retrieving literature..." },
      { progress: 40, status: "Analyzing abstracts..." },
      { progress: 60, status: "Computing similarity scores..." },
      { progress: 80, status: "Identifying research gaps..." },
      { progress: 100, status: "Generating final report..." },
    ];

    for (const stage of stages) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setState((prev) => ({
        ...prev,
        analysisProgress: stage.progress,
        analysisStatus: stage.status,
      }));
    }

    // Mock result
    const result: AnalysisResult = {
      noveltyScore: 87,
      relatedPapers: 23,
      keyGaps: 5,
      confidence: 92,
      novelAspects: [
        "Novel integration of transformer architecture with symbolic reasoning",
        "First application of neuro-symbolic AI to this specific domain",
        "Unique training methodology combining supervised and reinforcement learning",
        "Innovative evaluation metrics for hybrid AI systems",
      ],
      relatedWork: [
        "Chen et al. (2023) - 'Hybrid AI Systems for Scientific Discovery'",
        "Smith & Johnson (2022) - 'Neural-Symbolic Integration: A Survey'",
        "Wang et al. (2023) - 'Transformer-Based Reasoning Systems'",
        "Lee (2021) - 'Symbolic AI in Modern Machine Learning'",
      ],
      gaps: [
        "Limited scalability analysis for large-scale knowledge graphs",
        "Lack of benchmark datasets for hybrid reasoning tasks",
        "Insufficient exploration of multi-modal integration",
        "Missing real-world deployment case studies",
        "No comparison with recent foundation models",
      ],
      recommendations: [
        "Expand evaluation to include larger knowledge bases",
        "Create and publish benchmark datasets for reproducibility",
        "Explore integration with vision and language models",
        "Conduct user studies with domain experts",
        "Compare against GPT-4 and Claude for reasoning tasks",
      ],
    };

    await new Promise((resolve) => setTimeout(resolve, 500));

    setState((prev) => ({
      ...prev,
      isAnalyzing: false,
      analysisResult: result,
      analysisStatus: "Analysis complete!",
    }));

    return result;
  }, []);

  const resetAnalysis = useCallback(() => {
    setState(initialState);
  }, []);

  const getCompletedSteps = useCallback(() => {
    const completed: string[] = [];
    if (state.paperSections.length > 0) completed.push("paper");
    if (state.researchIdea.trim()) completed.push("idea");
    if (state.selectedDomains.length > 0) completed.push("domains");
    if (state.analysisResult) completed.push("analysis");
    return completed;
  }, [state.paperSections, state.researchIdea, state.selectedDomains, state.analysisResult]);

  return {
    state,
    addSection,
    removeSection,
    setResearchIdea,
    toggleDomain,
    addFile,
    removeFile,
    clearFiles,
    runAnalysis,
    resetAnalysis,
    getCompletedSteps,
  };
}
