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
import { useResearchState } from "@/hooks/useResearchState";

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

  return (
    <div className="min-h-screen relative overflow-hidden">
      <FloatingParticles />

      <GlobalToast
        show={showToast}
        onClose={() => setShowToast(false)}
        title="Analysis Complete"
        message="Your novelty assessment is ready. Open the Results tab to view findings."
      />

      <div className="relative z-10 min-h-screen flex flex-col">
        <HeroBanner />

        <div className="flex-1 px-4 pb-8 flex gap-6 max-w-[1600px] mx-auto w-full">
          {/* Sidebar */}
          <div className="hidden lg:block">
            <AppSidebar />
          </div>

          {/* Main Content */}
          <main className="flex-1 min-w-0" role="main">
            {/* Tabs Navigation */}
            <nav
              className="glass-card p-1.5 mb-8"
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
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
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

        {/* Footer */}
        <footer className="relative z-10 py-8 text-center border-t border-border/40">
          <p className="text-xs tracking-wide text-muted-foreground/80">
            <span className="font-serif font-semibold text-primary/90">
              Literature Review System
            </span>{" "}
            © 2026
            <span className="mx-3 opacity-40">•</span>
            Multi-Agent Intelligence Platform
            <span className="mx-3 opacity-40">•</span>
            <span className="rounded-md border border-primary/40 px-2 py-0.5 text-[11.5px] font-semibold uppercase tracking-wider text-primary/90">
            Designed & Developed by Prithvi
            </span>
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Index;
