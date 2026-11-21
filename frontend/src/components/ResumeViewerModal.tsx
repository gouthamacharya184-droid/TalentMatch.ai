import React, { useState, useEffect, useMemo } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  ExternalLink,
  Search,
  X,
  Eye,
  FileCode,
  FileCheck,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { resumesApi } from '../services/api';

export interface ResumeViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  resumeId?: string;
  candidateName?: string;
  filename?: string;
  rawText?: string;
}

export const ResumeViewerModal: React.FC<ResumeViewerModalProps> = ({
  isOpen,
  onClose,
  resumeId,
  candidateName,
  filename,
  rawText: initialRawText,
}) => {
  const [activeView, setActiveView] = useState<'preview' | 'text'>('preview');
  const [text, setText] = useState<string>(initialRawText || '');
  const [resolvedFilename, setResolvedFilename] = useState<string>(filename || 'Resume');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState(false);

  const isPdf = useMemo(() => {
    return resolvedFilename.toLowerCase().endsWith('.pdf');
  }, [resolvedFilename]);

  const fileExtension = useMemo(() => {
    const parts = resolvedFilename.split('.');
    return parts.length > 1 ? parts.pop()?.toUpperCase() : 'DOC';
  }, [resolvedFilename]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Load resume data / PDF blob
  useEffect(() => {
    if (!isOpen || !resumeId) return;

    let isMounted = true;
    let createdUrl: string | null = null;

    const loadData = async () => {
      setLoading(true);
      setPdfError(false);
      try {
        // 1. If text is missing, fetch full resume details
        if (!initialRawText) {
          try {
            const resumeData = await resumesApi.getResume(resumeId);
            if (isMounted && resumeData) {
              if (resumeData.raw_text) setText(resumeData.raw_text);
              if (resumeData.original_filename) setResolvedFilename(resumeData.original_filename);
            }
          } catch (e) {
            console.warn('Could not fetch resume details, trying fallback:', e);
          }
        } else {
          setText(initialRawText);
        }

        // 2. If it's a PDF, fetch binary blob for native PDF iframe viewer
        const looksLikePdf = (filename || resolvedFilename).toLowerCase().endsWith('.pdf');
        if (looksLikePdf) {
          try {
            const blob = await resumesApi.downloadResume(resumeId);
            if (isMounted) {
              const pdfBlob = new Blob([blob], { type: 'application/pdf' });
              createdUrl = URL.createObjectURL(pdfBlob);
              setPdfBlobUrl(createdUrl);
              setActiveView('preview');
            }
          } catch (err) {
            console.error('Failed to load PDF preview blob:', err);
            if (isMounted) {
              setPdfError(true);
              setActiveView('text');
            }
          }
        } else {
          // Non-PDF (DOCX/TXT) -> default to parsed formatted text view
          setActiveView('text');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();

    return () => {
      isMounted = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [isOpen, resumeId, initialRawText, filename, resolvedFilename]);

  const handleCopyText = async () => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy resume text:', e);
    }
  };

  const handleDownload = async () => {
    if (!resumeId) return;
    try {
      const blob = await resumesApi.downloadResume(resumeId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = resolvedFilename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Download failed:', e);
    }
  };

  const handleOpenInNewTab = () => {
    if (pdfBlobUrl) {
      window.open(pdfBlobUrl, '_blank');
    } else if (resumeId) {
      window.open(resumesApi.getResumeViewUrl(resumeId), '_blank');
    }
  };

  // Text stats
  const wordCount = typeof text === 'string' && text.trim() ? text.trim().split(/\s+/).length : 0;
  const lineCount = typeof text === 'string' && text.trim() ? text.split('\n').length : 0;

  // Highlight search matches in text
  const renderedContent = useMemo(() => {
    if (!text || typeof text !== 'string') return null;
    if (!searchQuery.trim()) {
      return text;
    }
    try {
      const escaped = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
      return parts.map((part, i) =>
        part.toLowerCase() === searchQuery.toLowerCase() ? (
          <mark key={i} className="bg-amber-300 text-slate-900 rounded-px px-0.5 font-semibold">
            {part}
          </mark>
        ) : (
          part
        )
      );
    } catch {
      return text;
    }
  }, [text, searchQuery]);

  if (!isOpen) return null;

  return (
    <div
      id="resume-viewer-modal"
      className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-3 sm:p-6 overflow-hidden animate-in fade-in duration-150"
    >
      <div className="bg-white rounded-2xl w-full max-w-5xl h-[92vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header Bar */}
        <div className="p-4 sm:px-6 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-white to-blue-50/40 flex items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-blue-600/10 text-blue-600 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 truncate">
                  {candidateName ? `${candidateName}'s Resume` : 'Resume Document Viewer'}
                </h3>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold tracking-wide uppercase bg-blue-100 text-blue-700 shrink-0">
                  {fileExtension}
                </span>
              </div>
              <p className="text-xs text-slate-500 truncate mt-0.5" title={resolvedFilename}>
                {resolvedFilename}
              </p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2 shrink-0">
            {/* View Mode Toggle (If PDF) */}
            {isPdf && !pdfError && (
              <div className="hidden sm:flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
                <button
                  onClick={() => setActiveView('preview')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                    activeView === 'preview'
                      ? 'bg-white text-blue-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>PDF View</span>
                </button>
                <button
                  onClick={() => setActiveView('text')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                    activeView === 'text'
                      ? 'bg-white text-blue-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>Parsed Text</span>
                </button>
              </div>
            )}

            {/* Copy Text Button */}
            {text && (
              <button
                onClick={handleCopyText}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs font-medium transition-colors shadow-sm"
                title="Copy parsed text to clipboard"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700 font-semibold">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                    <span className="hidden sm:inline">Copy Text</span>
                  </>
                )}
              </button>
            )}

            {/* Open In New Tab */}
            <button
              onClick={handleOpenInNewTab}
              className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
              title="Open document in new browser tab"
            >
              <ExternalLink className="w-4 h-4 text-slate-500" />
            </button>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-colors"
              title="Download original file"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download</span>
            </button>

            {/* Close */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors ml-1"
              title="Close viewer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Search Bar for Parsed Text View */}
        {activeView === 'text' && text && (
          <div className="px-6 py-2.5 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search skills, companies, keywords in resume..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
              />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span>
                <strong>{wordCount}</strong> words
              </span>
              <span>•</span>
              <span>
                <strong>{lineCount}</strong> lines
              </span>
            </div>
          </div>
        )}

        {/* Viewer Body */}
        <div className="flex-1 bg-slate-100 overflow-hidden relative">
          {loading && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              <p className="text-xs font-semibold text-slate-600">Loading Resume Document...</p>
            </div>
          )}

          {/* VIEW 1: Native PDF Iframe */}
          {activeView === 'preview' && isPdf && pdfBlobUrl && !pdfError ? (
            <div className="w-full h-full p-2">
              <iframe
                src={`${pdfBlobUrl}#toolbar=1&navpanes=0`}
                className="w-full h-full rounded-xl border border-slate-300 bg-white shadow-inner"
                title="Resume PDF Viewer"
              />
            </div>
          ) : activeView === 'preview' && isPdf && pdfError ? (
            <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-white">
              <AlertCircle className="w-12 h-12 text-amber-500 mb-3" />
              <h4 className="text-sm font-bold text-slate-900 mb-1">
                Unable to render embedded PDF preview
              </h4>
              <p className="text-xs text-slate-500 max-w-md mb-4">
                The document is available in extracted text mode, or you can download the original file to view it locally.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveView('text')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
                >
                  Switch to Text View
                </button>
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50"
                >
                  Download File
                </button>
              </div>
            </div>
          ) : (
            /* VIEW 2: Formatted Document Text View (For DOCX, TXT, or text mode) */
            <div className="w-full h-full overflow-y-auto p-4 sm:p-8">
              <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md border border-slate-200 p-8 sm:p-12 min-h-full">
                {/* Document Top Badge */}
                <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-100 text-xs text-slate-400">
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-emerald-600" />
                    <span className="font-medium text-slate-700">Verified Uploaded Document</span>
                  </div>
                  <span>Original format: {fileExtension}</span>
                </div>

                {/* Formatted Content */}
                {text ? (
                  <pre className="whitespace-pre-wrap font-sans text-xs sm:text-sm text-slate-800 leading-relaxed selection:bg-blue-100 selection:text-blue-900">
                    {renderedContent}
                  </pre>
                ) : (
                  <div className="py-16 text-center text-slate-400 text-xs">
                    <FileText className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                    <p>No extracted text available for this document.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Document loaded from secure storage</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-medium transition-colors"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
};
