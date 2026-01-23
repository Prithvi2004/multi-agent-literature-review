/**
 * Keyboard Shortcuts Hook
 * Provides comprehensive keyboard navigation for the application
 */

import { useEffect, useCallback } from 'react';

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

const shortcuts: ShortcutConfig[] = [];

export function useKeyboardShortcuts(config: {
  onRunAnalysis?: () => void;
  onToggleTerminal?: () => void;
  onSwitchTab?: (tabId: string) => void;
  onSaveSession?: () => void;
  onFocusSearch?: () => void;
  onExport?: (format: string) => void;
}) {
  const handleKeyPress = useCallback((event: KeyboardEvent) => {
    // Ctrl+Enter: Run analysis
    if (event.ctrlKey && event.key === 'Enter' && config.onRunAnalysis) {
      event.preventDefault();
      config.onRunAnalysis();
      return;
    }

    // Ctrl+T: Toggle terminal
    if (event.ctrlKey && event.key === 't' && config.onToggleTerminal) {
      event.preventDefault();
      config.onToggleTerminal();
      return;
    }

    // Ctrl+1/2/3: Switch tabs
    if (event.ctrlKey && ['1', '2', '3'].includes(event.key) && config.onSwitchTab) {
      event.preventDefault();
      const tabMap: Record<string, string> = { '1': 'input', '2': 'results', '3': 'library' };
      config.onSwitchTab(tabMap[event.key]);
      return;
    }

    // Ctrl+S: Save session
    if (event.ctrlKey && event.key === 's' && config.onSaveSession) {
      event.preventDefault();
      config.onSaveSession();
      return;
    }

    // /: Focus search
    if (event.key === '/' && config.onFocusSearch && !isInputFocused()) {
      event.preventDefault();
      config.onFocusSearch();
      return;
    }

    // Ctrl+E: Export (shows menu)
    if (event.ctrlKey && event.key === 'e' && config.onExport) {
      event.preventDefault();
      config.onExport('markdown'); // Default to markdown
      return;
    }
  }, [config]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  return {
    shortcuts: [
      { key: 'Ctrl+Enter', description: 'Run analysis' },
      { key: 'Ctrl+T', description: 'Toggle terminal' },
      { key: 'Ctrl+1/2/3', description: 'Switch tabs' },
      { key: 'Ctrl+S', description: 'Save session' },
      { key: '/', description: 'Focus search' },
      { key: 'Ctrl+E', description: 'Export' },
    ]
  };
}

function isInputFocused(): boolean {
  const activeElement = document.activeElement;
  return activeElement?.tagName === 'INPUT' || 
         activeElement?.tagName === 'TEXTAREA' ||
         activeElement?.getAttribute('contenteditable') === 'true';
}
