/**
 * Session Manager Component
 * Displays saved sessions and provides session management UI
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Save,
  FolderOpen,
  Trash2,
  Plus,
  Clock,
  FileText,
  Layers,
} from 'lucide-react';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';
import { formatDistanceToNow } from 'date-fns';
import { GradientButton } from './ui/GradientButton';

interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  metadata: {
    auto_saved?: boolean;
    sections_count?: number;
    domains_count?: number;
    has_analysis?: boolean;
  };
}

interface SessionManagerProps {
  sessions: Session[];
  currentSessionId: string | null;
  lastSaved: Date | null;
  onSave: (name?: string, isAutoSave?: boolean) => Promise<string>;
  onLoad: (sessionId: string) => Promise<void>;
  onDelete: (sessionId: string) => Promise<void>;
  onNew: () => void;
}

export function SessionManager({
  sessions,
  currentSessionId,
  lastSaved,
  onSave,
  onLoad,
  onDelete,
  onNew,
}: SessionManagerProps) {
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await onSave(sessionName || undefined);
      setSessionName('');
      setIsSaveDialogOpen(false);
    } catch (error) {
      console.error('Failed to save session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoad = async (sessionId: string) => {
    setIsLoading(true);
    try {
      await onLoad(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this session?')) {
      setIsLoading(true);
      try {
        await onDelete(sessionId);
      } catch (error) {
        console.error('Failed to delete session:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-border/30">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-primary/10">
            <FolderOpen className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground text-sm">Sessions</h3>
            {lastSaved && (
              <p className="text-xs text-muted-foreground">
                Saved {formatDistanceToNow(lastSaved, { addSuffix: true })}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2">
        <GradientButton
          onClick={() => setIsSaveDialogOpen(true)}
          size="sm"
          icon={<Save className="h-3.5 w-3.5" />}
          disabled={isLoading}
          className="w-full"
        >
          Save
        </GradientButton>
        <GradientButton
          onClick={onNew}
          size="sm"
          variant="ghost"
          icon={<Plus className="h-3.5 w-3.5" />}
          disabled={isLoading}
          className="w-full"
        >
          New
        </GradientButton>
      </div>

      {/* Sessions List */}
      <ScrollArea className="max-h-[400px]">
        <div className="space-y-2 pr-2">
          <AnimatePresence>
            {sessions.length === 0 ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center py-8 text-muted-foreground text-sm"
              >
                No saved sessions yet
              </motion.div>
            ) : (
              sessions.map((session) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`group p-3 rounded-lg border transition-all cursor-pointer hover:shadow-md ${
                    currentSessionId === session.id
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border hover:border-primary/50 hover:bg-muted/30'
                  }`}
                  onClick={() => handleLoad(session.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-foreground truncate mb-1">
                        {session.name}
                      </p>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
                        <Clock className="h-3 w-3" />
                        <span>
                          {formatDistanceToNow(new Date(session.updated_at), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {session.metadata.sections_count !== undefined && (
                          <Badge variant="secondary" className="text-xs px-2 py-0.5">
                            <FileText className="h-2.5 w-2.5 mr-1" />
                            {session.metadata.sections_count}
                          </Badge>
                        )}
                        {session.metadata.domains_count !== undefined && (
                          <Badge variant="secondary" className="text-xs px-2 py-0.5">
                            <Layers className="h-2.5 w-2.5 mr-1" />
                            {session.metadata.domains_count}
                          </Badge>
                        )}
                        {session.metadata.auto_saved && (
                          <Badge variant="outline" className="text-xs px-2 py-0.5">
                            Auto
                          </Badge>
                        )}
                      </div>
                    </div>
                    <GradientButton
                      onClick={(e) => handleDelete(session.id, e)}
                      size="sm"
                      variant="danger"
                      icon={<Trash2 className="h-3 w-3" />}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Delete
                    </GradientButton>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Save Dialog */}
      <Dialog open={isSaveDialogOpen} onOpenChange={setIsSaveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Session</DialogTitle>
            <DialogDescription>
              Give your session a name to easily find it later.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="e.g., Transformer Architecture Review"
            value={sessionName}
            onChange={(e) => setSessionName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSave();
              }
            }}
          />
          <DialogFooter>
            <GradientButton
              onClick={() => setIsSaveDialogOpen(false)}
              variant="ghost"
              disabled={isLoading}
            >
              Cancel
            </GradientButton>
            <GradientButton onClick={handleSave} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Session'}
            </GradientButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
