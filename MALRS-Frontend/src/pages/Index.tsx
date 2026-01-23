import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings2, BarChart3, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

import { FloatingParticles } from "@/components/FloatingParticles";
import { HeroBanner } from "@/components/HeroBanner";
import { AppSidebar } from "@/components/AppSidebar";
import { InputConfigureTab } from "@/components/tabs/InputConfigureTab";
import { ResultsTab } from "@/components/tabs/ResultsTab";
import { LibraryTab } from "@/components/tabs/LibraryTab";
import { GlobalToast } from "@/components/GlobalToast";
import { SessionManager } from "@/components/SessionManager";
import { ResearchChat } from "@/components/ResearchChat";
import { useResearchState } from "@/hooks/useResearchState";
import { useSessionPersistence } from "@/hooks/useSessionPersistence";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";

const tabs = [
  { id: "input", label: "Input & Configure", icon: Settings2 },
  { id: "results", label: "Results & Analysis", icon: BarChart3 },
  { id: "library", label: "Paper Library", icon: BookOpen },
];

const Index = () => {
  const [activeTab, setActiveTab] = useState("input");
  const [showToast, setShowToast] = useState(false);

  const {
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
  } = useResearchState();

  // Define handler functions first
  const handleRunAnalysis = async () => {
    await runAnalysis();
    setShowToast(true);
    // Switch to results tab after analysis
    setTimeout(() => {
      setActiveTab("results");
    }, 1000);
  };

  const handleReset = () => {
    resetAnalysis();
    setActiveTab("input");
  };

  const handleLoadSession = async (sessionId: string) => {
    const session = await loadSession(sessionId);
    if (session) {
      // Load session data into state
      setResearchIdea(session.research_idea);
      // Note: You'll need to add methods to load other session data
      console.log("Session loaded:", session);
    }
  };

  // Session persistence
  const {
    sessions,
    currentSessionId,
    lastSaved,
    saveSession,
    loadSession,
    deleteSession,
    newSession,
  } = useSessionPersistence(state);

  // Keyboard shortcuts - now handleRunAnalysis is defined
  useKeyboardShortcuts({
    onRunAnalysis: handleRunAnalysis,
    onSwitchTab: setActiveTab,
    onSaveSession: () => saveSession().catch(console.error),
  });

  return (
    <div className="min-h-screen relative overflow-hidden bg-background">
      <FloatingParticles />

      <GlobalToast
        show={showToast}
        onClose={() => setShowToast(false)}
        title="Analysis Complete"
        message="Your novelty assessment is ready. Open the Results tab to view findings."
      />

      {/* AI Research Chat - Floating Widget */}
      {state.analysisResult && (
        <ResearchChat
          analysisContext={{
            research_idea: state.researchIdea,
            papers: state.analysisResult?.retrievedPapers || [],
            final_report: state.analysisResult?.fullReport || "",
          }}
        />
      )}

      <div className="relative z-10 min-h-screen flex flex-col">
        <HeroBanner />

        {/* Main Content Container */}
        <div className="flex-1 container mx-auto px-4 pb-8 max-w-[1800px]">
          <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
            
            {/* Integrated Sidebar */}
            <AppSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              lastSaved={lastSaved}
              onSave={saveSession}
              onLoad={handleLoadSession}
              onDelete={deleteSession}
              onNew={newSession}
            />

            {/* Main Content Area */}
            <main className="min-w-0" role="main">
              {/* Tabs Navigation */}
              <nav
                className="glass-card p-1.5 mb-6 sticky top-4 z-20"
                role="tablist"
                aria-label="Main navigation"
              >
                <div className="flex gap-1">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                      <motion.button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                          "relative flex-1 flex items-center justify-center gap-2.5 px-5 py-3.5 rounded font-medium text-sm transition-all duration-300",
                          isActive
                            ? "text-primary-foreground shadow-lg"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted/40",
                        )}
                        role="tab"
                        aria-selected={isActive}
                        aria-controls={`${tab.id}-panel`}
                        whileTap={{ scale: 0.97 }}
                      >
                        {isActive && (
                          <motion.div
                            className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-secondary/80 rounded"
                            layoutId="activeTab"
                            transition={{
                              type: "spring",
                              stiffness: 400,
                              damping: 35,
                            }}
                            style={{
                              boxShadow:
                                "0 0 20px hsla(38, 92%, 58%, 0.3), inset 0 1px 0 hsla(40, 100%, 70%, 0.2)",
                            }}
                          />
                        )}
                        <span className="relative z-10 flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          <span className="hidden sm:inline">{tab.label}</span>
                        </span>
                      </motion.button>
                    );
                  })}
                </div>
              </nav>

              {/* Tab Panels */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  role="tabpanel"
                  id={`${activeTab}-panel`}
                  aria-labelledby={activeTab}
                >
                  {activeTab === "input" && (
                    <InputConfigureTab
                      paperSections={state.paperSections}
                      researchIdea={state.researchIdea}
                      selectedDomains={state.selectedDomains}
                      uploadedFiles={state.uploadedFiles}
                      isAnalyzing={state.isAnalyzing}
                      analysisProgress={state.analysisProgress}
                      analysisStatus={state.analysisStatus}
                      completedSteps={getCompletedSteps()}
                      onAddSection={addSection}
                      onRemoveSection={removeSection}
                      onSetResearchIdea={setResearchIdea}
                      onToggleDomain={toggleDomain}
                      onRunAnalysis={handleRunAnalysis}
                    />
                  )}

                  {activeTab === "results" && (
                    <ResultsTab
                      analysisResult={state.analysisResult}
                      onReset={handleReset}
                      isAnalyzing={state.isAnalyzing}
                    />
                  )}

                  {activeTab === "library" && (
                    <LibraryTab
                      uploadedFiles={state.uploadedFiles}
                      onAddFile={addFile}
                      onRemoveFile={removeFile}
                      onClearFiles={clearFiles}
                    />
                  )}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>
        </div>

        {/* Footer */}
        <footer className="relative z-10 py-6 mt-auto border-t border-border/40 bg-background/50 backdrop-blur-sm">
          <div className="container mx-auto px-4 max-w-[1800px]">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-xs tracking-wide text-muted-foreground/80 text-center sm:text-left">
                <span className="font-serif font-semibold text-primary/90">
                  Literature Review System
                </span>{" "}
                © 2025
                <span className="mx-2 opacity-40">•</span>
                Multi-Agent Intelligence Platform
                <span className="mx-2 opacity-40">•</span>
                Crafted by Prithvi
              </p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
                <kbd className="px-2 py-1 bg-muted/50 rounded text-xs">Ctrl+1/2/3</kbd>
                <span>Switch tabs</span>
                <span className="mx-1">•</span>
                <kbd className="px-2 py-1 bg-muted/50 rounded text-xs">Ctrl+S</kbd>
                <span>Save</span>
                <span className="mx-1">•</span>
                <kbd className="px-2 py-1 bg-muted/50 rounded text-xs">Ctrl+Enter</kbd>
                <span>Analyze</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Index;
