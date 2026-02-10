/**
 * API Service for Multi-Agent Literature Review
 * Connects React frontend to Flask backend
 */

// Use relative path for development (Vite proxy) or absolute URL for production
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface AnalyzeRequest {
  research_idea: string;
  selected_domains: string[];
  paper_data?: {
    paper_sections: Array<{
      field: string;
      content: string;
    }>;
    uploaded_papers: any[];
  };
}

export interface AnalyzeResponse {
  status: 'success' | 'error';
  message: string;
    data?: {
    final_report: string;
    detailed_agent_analysis: string;
    agent_outputs: {
      retrieval: string;
      decomposition: string;
      reasoning: string;
      gap_novelty: string;
      synthesis: string;
    };
    papers: Array<{
      handle: string;
      title: string;
      authors: string;
      year: string | number;
      abstract: string;
    }>;
    metrics: {
      total_duration_seconds: number;
      total_papers_retrieved: number;
      total_agents: number;
    };
    frontend_metrics?: {
      novelty_score: number;
      related_papers_count: number;
      key_gaps_count: number;
      confidence_score: number;
    };
  };
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Run analysis on research data
   */
  async analyze(
    request: AnalyzeRequest,
    onProgress?: (status: string, progress: number) => void
  ): Promise<AnalyzeResponse> {
    // Simulate progress updates during the API call
    const progressInterval = onProgress ? this.simulateProgress(onProgress) : null;

    try {
      const response = await fetch(`${this.baseUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      // Clear progress simulation
      if (progressInterval) {
        clearInterval(progressInterval);
      }

      const data: AnalyzeResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `API request failed: ${response.statusText}`);
      }

      return data;
    } catch (error) {
      // Clear progress simulation on error
      if (progressInterval) {
        clearInterval(progressInterval);
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(
          'Cannot connect to the backend API. Please ensure the Flask server is running on ' + this.baseUrl
        );
      }

      throw error;
    }
  }

  /**
   * Simulate progress updates during analysis
   */
  private simulateProgress(
    onProgress: (status: string, progress: number) => void
  ): NodeJS.Timeout {
    const stages = [
      { progress: 10, status: 'Connecting to backend...' },
      { progress: 20, status: 'Sending analysis request...' },
      { progress: 30, status: 'Retrieving relevant literature...' },
      { progress: 50, status: 'Multi-agent analysis in progress...' },
      { progress: 70, status: 'Processing results...' },
      { progress: 85, status: 'Finalizing report...' },
    ];

    let currentStage = 0;

    const interval = setInterval(() => {
      if (currentStage < stages.length) {
        const stage = stages[currentStage];
        onProgress(stage.status, stage.progress);
        currentStage++;
      }
    }, 3000); // Update every 3 seconds

    return interval;
  }

  /**
   * Test if the API is reachable
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export class for testing
export default ApiService;
