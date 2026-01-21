import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  Download,
  Trash2,
  HardDrive,
  FolderOpen,
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { GradientButton } from "@/components/ui/GradientButton";
import { UploadedFile } from "@/hooks/useResearchState";

interface LibraryTabProps {
  uploadedFiles: UploadedFile[];
  onAddFile: (file: File) => void;
  onRemoveFile: (id: string) => void;
  onClearFiles: () => void;
}

export function LibraryTab({
  uploadedFiles,
  onAddFile,
  onRemoveFile,
  onClearFiles,
}: LibraryTabProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      files
        .filter((f) => f.type === "application/pdf")
        .forEach((file) => onAddFile(file));
    },
    [onAddFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      files.forEach((file) => onAddFile(file));
    },
    [onAddFile]
  );

  const totalSize = uploadedFiles.reduce((acc, f) => acc + f.size, 0);
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <GlassCard
        className="border-2 border-dashed border-border/50 hover:border-primary/50 transition-colors cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <label className="block text-center py-8 cursor-pointer">
          <input
            type="file"
            accept=".pdf"
            multiple
            className="hidden"
            onChange={handleFileInput}
            aria-label="Upload PDF files"
          />
          <motion.div
            className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center"
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <Upload className="h-8 w-8 text-primary" />
          </motion.div>
          <h3 className="heading-md text-foreground mb-2">
            Upload Research Papers
          </h3>
          <p className="body-md text-muted-foreground">
            Drag and drop PDF files here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground/60 mt-2">
            Supported format: PDF
          </p>
        </label>
      </GlassCard>

      {/* Uploaded Files List */}
      <AnimatePresence>
        {uploadedFiles.length > 0 ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-primary" />
                Uploaded Papers
              </h3>
            </div>

            {uploadedFiles.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <GlassCard className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-accent/10">
                        <FileText className="h-5 w-5 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground text-sm">
                          {file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatSize(file.size)} • {file.type || "PDF"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <GradientButton
                        variant="ghost"
                        size="sm"
                        icon={<Download className="h-4 w-4" />}
                        onClick={() => {
                          // Simulate download
                          console.log("Downloading:", file.name);
                        }}
                      >
                        Download
                      </GradientButton>
                      <GradientButton
                        variant="danger"
                        size="sm"
                        icon={<Trash2 className="h-4 w-4" />}
                        onClick={() => onRemoveFile(file.id)}
                      >
                        Remove
                      </GradientButton>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        ) : (
          <GlassCard className="text-center py-12">
            <FolderOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold text-foreground mb-2">
              No Papers Uploaded
            </h3>
            <p className="text-sm text-muted-foreground">
              Upload PDF files to build your research library
            </p>
          </GlassCard>
        )}
      </AnimatePresence>

      {/* Library Stats Footer */}
      {uploadedFiles.length > 0 && (
        <GlassCard>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <HardDrive className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Total Papers:{" "}
                  <span className="text-foreground font-medium">
                    {uploadedFiles.length}
                  </span>
                </span>
              </div>
              <div className="h-4 w-px bg-border" />
              <span className="text-sm text-muted-foreground">
                Total Size:{" "}
                <span className="text-foreground font-medium">
                  {formatSize(totalSize)}
                </span>
              </span>
            </div>
            <GradientButton
              variant="danger"
              size="sm"
              icon={<Trash2 className="h-4 w-4" />}
              onClick={onClearFiles}
            >
              Clear All
            </GradientButton>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
