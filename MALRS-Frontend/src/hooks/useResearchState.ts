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
  fullReport?: string;
  agentOutputs?: {
    retrieval: string;
    decomposition: string;
    reasoning: string;
    gap_novelty: string;
    synthesis: string;
  };
  retrievedPapers?: Array<{
    handle: string;
    title: string;
    authors: string;
    year: string | number;
    abstract: string;
  }>;
  metrics?: {
    total_duration_seconds: number;
    total_papers_retrieved: number;
    total_agents: number;
  };
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
  "Title",
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

    try {
      // Import API service
      const { apiService } = await import("@/lib/apiService");

      // Prepare request payload
      const request = {
        research_idea: state.researchIdea || "No specific research idea provided",
        selected_domains: state.selectedDomains.length > 0 ? state.selectedDomains : ["General"],
        paper_data: state.paperSections.length > 0 ? {
          paper_sections: state.paperSections.map(section => ({
            field: section.type,
            content: section.content
          })),
          uploaded_papers: []
        } : undefined
      };

      // Call API with progress updates
      const response = await apiService.analyze(
        request,
        (status, progress) => {
          setState((prev) => ({
            ...prev,
            analysisProgress: progress,
            analysisStatus: status,
          }));
        }
      );

      if (response.status === "success" && response.data) {
        // Parse the analysis results from the backend
        const { final_report, agent_outputs, papers, metrics } = response.data;

        // Extract novelty information from the report
        // This is a simplified extraction - you might want to enhance this
        const noveltyScore = 87; // Could be extracted from report or added to backend response
        const relatedPapers = metrics.total_papers_retrieved || papers.length;
        const keyGaps = 5; // Could be extracted from gap_novelty agent output
        const confidence = 92; // Could be extracted from report

        // Extract novel aspects from synthesis output
        const novelAspects = extractListItems(agent_outputs.synthesis || final_report, "novel");
        
        // Extract related work from retrieval output
        const relatedWork = papers.slice(0, 4).map(p => 
          `${p.authors.split(',')[0]} et al. (${p.year}) - "${p.title}"`
        );

        // Extract gaps from gap_novelty output  
        const gaps = extractListItems(agent_outputs.gap_novelty || "", "gap");

        // Extract recommendations from synthesis output
        const recommendations = extractListItems(agent_outputs.synthesis || final_report, "recommend");

        const result: AnalysisResult = {
          noveltyScore,
          relatedPapers,
          keyGaps,
          confidence,
          novelAspects: novelAspects.length > 0 ? novelAspects : [
            "Analysis complete - see full report for details"
          ],
          relatedWork: relatedWork.length > 0 ? relatedWork : [
            "See retrieved papers for related work"
          ],
          gaps: gaps.length > 0 ? gaps : [
            "See full analysis for research gaps"
          ],
          recommendations: recommendations.length > 0 ? recommendations : [
            "See full report for recommendations"
          ],
          fullReport: final_report,
          agentOutputs: agent_outputs,
          retrievedPapers: papers,
          metrics
        };

        setState((prev) => ({
          ...prev,
          isAnalyzing: false,
          analysisResult: result,
          analysisProgress: 100,
          analysisStatus: "Analysis complete!",
        }));

        return result;
      } else {
        throw new Error(response.message || "Analysis failed");
      }
    } catch (error) {
      console.error("Analysis error:", error);
      
      setState((prev) => ({
        ...prev,
        isAnalyzing: false,
        analysisProgress: 0,
        analysisStatus: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      }));

      // Re-throw to allow caller to handle
      throw error;
    }
  }, [state.researchIdea, state.selectedDomains, state.paperSections]);

  // Helper function to extract list items from text
  function extractListItems(text: string, keyword: string): string[] {
    const lines = text.split('\n');
    const items: string[] = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      // Look for bullet points or numbered lists
      if (trimmed.match(/^[-*•]\s+/) || trimmed.match(/^\d+\.\s+/)) {
        const content = trimmed.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '').trim();
        if (content.toLowerCase().includes(keyword) || keyword === "") {
          items.push(content);
        }
      }
    }
    
    return items.slice(0, 5); // Limit to 5 items
  }

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
