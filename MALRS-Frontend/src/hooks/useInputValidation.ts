/**
 * Input Validation Hook
 * Provides real-time validation and AI-powered suggestions for research inputs
 */

import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';

interface ValidationResult {
  isValid: boolean;
  score: number; // 0-100
  issues: string[];
  suggestions: string[];
}

interface ValidationState {
  researchIdea: ValidationResult | null;
  isValidating: boolean;
}

const MIN_IDEA_LENGTH = 20;
const MAX_IDEA_LENGTH = 1000;

/**
 * Validate research idea locally (fast checks)
 */
const validateLocally = (text: string): Partial<ValidationResult> => {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 100;

  // Length checks
  if (text.length < MIN_IDEA_LENGTH) {
    issues.push(`Too short (${text.length}/${MIN_IDEA_LENGTH} characters)`);
    suggestions.push('Provide more details about your research question');
    score -= 30;
  } else if (text.length > MAX_IDEA_LENGTH) {
    issues.push(`Too long (${text.length}/${MAX_IDEA_LENGTH} characters)`);
    suggestions.push('Try to be more concise and focused');
    score -= 20;
  }

  // Content quality checks
  const wordCount = text.trim().split(/\s+/).length;
  if (wordCount < 5) {
    issues.push('Too few words');
    suggestions.push('Elaborate on your research idea');
    score -= 25;
  }

  // Check for question marks (research questions are good)
  if (!text.includes('?') && wordCount > 10) {
    suggestions.push('Consider framing as a research question');
  }

  // Check for specific terms
  const hasMethodology = /\b(using|applying|leveraging|implementing|developing)\b/i.test(text);
  const hasDomain = /\b(machine learning|AI|NLP|computer vision|data|neural|deep learning)\b/i.test(text);
  
  if (!hasMethodology) {
    suggestions.push('Consider mentioning the methodology or approach');
    score -= 10;
  }

  if (!hasDomain) {
    suggestions.push('Specify the research domain or field');
    score -= 10;
  }

  // Check for vague terms
  const vagueTerms = ['good', 'better', 'improve', 'enhance', 'optimize'];
  const hasVagueTerms = vagueTerms.some(term => 
    new RegExp(`\\b${term}\\b`, 'i').test(text)
  );
  
  if (hasVagueTerms) {
    suggestions.push('Be more specific about what you want to achieve');
    score -= 5;
  }

  return {
    score: Math.max(0, Math.min(100, score)),
    issues,
    suggestions
  };
};

/**
 * Validate research idea with AI (backend call)
 */
const validateWithAI = async (text: string): Promise<ValidationResult> => {
  try {
    const response = await fetch('http://localhost:5000/api/validate-input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ research_idea: text }),
    });

    if (!response.ok) {
      throw new Error('Validation failed');
    }

    const data = await response.json();
    return data.validation;
  } catch (error) {
    console.warn('AI validation unavailable, using local validation only');
    // Fallback to local validation
    const local = validateLocally(text);
    return {
      isValid: (local.score || 0) >= 60,
      score: local.score || 0,
      issues: local.issues || [],
      suggestions: local.suggestions || []
    };
  }
};

/**
 * Input Validation Hook
 */
export function useInputValidation() {
  const [state, setState] = useState<ValidationState>({
    researchIdea: null,
    isValidating: false,
  });

  // Debounced AI validation (only call after user stops typing)
  const debouncedAIValidation = useCallback(
    debounce(async (text: string) => {
      if (!text.trim()) {
        setState(prev => ({ ...prev, researchIdea: null, isValidating: false }));
        return;
      }

      const result = await validateWithAI(text);
      setState(prev => ({
        ...prev,
        researchIdea: result,
        isValidating: false,
      }));
    }, 1500), // Wait 1.5s after user stops typing
    []
  );

  /**
   * Validate research idea
   */
  const validateResearchIdea = useCallback((text: string) => {
    // Immediate local validation
    const local = validateLocally(text);
    setState(prev => ({
      ...prev,
      researchIdea: {
        isValid: (local.score || 0) >= 60,
        score: local.score || 0,
        issues: local.issues || [],
        suggestions: local.suggestions || []
      },
      isValidating: true,
    }));

    // Trigger debounced AI validation
    debouncedAIValidation(text);
  }, [debouncedAIValidation]);

  /**
   * Accept a suggestion (apply it to the input)
   */
  const acceptSuggestion = useCallback((suggestion: string, currentText: string): string => {
    // Smart suggestion application
    if (suggestion.includes('question')) {
      // Add question mark if not present
      return currentText.trim().endsWith('?') ? currentText : currentText + '?';
    }
    
    // For other suggestions, just return the current text
    // (User will manually apply the suggestion)
    return currentText;
  }, []);

  return {
    validationState: state,
    validateResearchIdea,
    acceptSuggestion,
  };
}
