import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Cpu,
  Trash2,
  RefreshCw,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Clock,
  Layers,
  WifiOff
} from 'lucide-react';
import { resumesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { formatApiError } from '../utils/errors';
import type { Resume, Candidate } from '../types';

export type QueueStatus = 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';

export interface UploadItem {
  id: string;
  file: File;
  name: string;
  size: number;
  status: QueueStatus;
  progress?: number;
  error?: string;
  resumeData?: Resume;
}

const MAX_FILE_SIZE_BYTES = 4.5 * 1024 * 1024; // 4.5 MB (Vercel serverless request body limit)
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt'];

export const ResumeUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { isOffline, checkBackendHealth } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [batchSuccess, setBatchSuccess] = useState<string | null>(null);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const handleContinueToMatching = () => {
    const completedItems = items.filter((i) => i.status === 'completed' && i.resumeData?.candidate_id);
    const completedCandidateIds = completedItems
      .map((i) => i.resumeData!.candidate_id!)
      .filter(Boolean);
    const uploadedCandidates: Candidate[] = completedItems.map((i) => ({
      id: i.resumeData!.candidate_id!,
      name: i.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '),
      email: `${i.name.replace(/\.[^/.]+$/, '').toLowerCase().replace(/[^a-z0-9]/g, '')}@applicant.io`,
      phone: '',
      location: 'Uploaded Resume',
      total_experience_years: 3.5,
      education: null,
      extracted_profile: null,
      status: 'new' as const,
      skills: [],
      created_at: new Date().toISOString(),
    }));
    navigate('/matching', {
      state: {
        candidateIds: completedCandidateIds,
        uploadedCandidates,
        fromUpload: true,
        count: completedCount,
      },
    });
  };

  const handleLoadSampleBatch = async () => {
    setLoadingSamples(true);
    setBatchError(null);
    setBatchSuccess(null);
    try {
      const results = await resumesApi.loadSampleBatch();
      const safeList = Array.isArray(results) ? results : (results ? [results] : []);
      const newItems: UploadItem[] = safeList.map((r) => ({
        id: r.id || Math.random().toString(36).substring(2, 9),
        file: new File([], r.original_filename || 'demo_resume.pdf'),
        name: r.original_filename || 'demo_resume.pdf',
        size: r.file_size || 0,
        status: (r.processing_status === 'completed' || r.status === 'completed') ? 'completed' : 'failed',
        error: r.error_message || undefined,
        resumeData: r,
      }));
      setItems((prev) => {
        // Merge without duplicating filenames
        const existingNames = new Set(prev.map((p) => p.name));
        const filteredNew = newItems.filter((n) => !existingNames.has(n.name));
        return [...prev, ...filteredNew];
      });
      const completedSamples = newItems.filter((i) => i.status === 'completed').length;
      setBatchSuccess(`Successfully loaded ${completedSamples} demo resumes ready for candidate evaluation.`);
    } catch (err: any) {
      setBatchError(formatApiError(err, 'Failed to load sample resumes.'));
    } finally {
      setLoadingSamples(false);
    }
  };

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setBatchError(null);
    setBatchSuccess(null);

    if (items.length + fileList.length > 50) {
      setBatchError(`Maximum 50 resumes allowed in a single batch. You currently have ${items.length} in queue.`);
      return;
    }

    const newItems: UploadItem[] = [];
    const seenInBatch = new Set<string>();

    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i];
      const lastDot = f.name.lastIndexOf('.');
      const ext = lastDot >= 0 ? f.name.substring(lastDot).toLowerCase() : '';
      const fileKey = `${f.name}-${f.size}`;

      // Check duplicate within the same selection batch
      if (seenInBatch.has(fileKey)) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file: f,
          name: f.name,
          size: f.size,
          status: 'failed',
          error: 'Duplicate file within the same batch',
        });
        continue;
      }
      seenInBatch.add(fileKey);

      // Check duplicate in existing queue
      const isAlreadyInQueue = items.some((item) => item.name === f.name && item.size === f.size);
      if (isAlreadyInQueue) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file: f,
          name: f.name,
          size: f.size,
          status: 'failed',
          error: 'File already exists in upload queue',
        });
        continue;
      }

      // Check file extension
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file: f,
          name: f.name,
          size: f.size,
          status: 'failed',
          error: `Unsupported format '${ext}'. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`,
        });
        continue;
      }

      // Check file size (15 MB maximum)
      if (f.size > MAX_FILE_SIZE_BYTES) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file: f,
          name: f.name,
          size: f.size,
          status: 'failed',
          error: `File size exceeds 4.5 MB serverless limit (${(f.size / (1024 * 1024)).toFixed(1)} MB)`,
        });
        continue;
      }

      // Check empty file
      if (f.size === 0) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file: f,
          name: f.name,
          size: 0,
          status: 'failed',
          error: 'File is empty (0 bytes)',
        });
        continue;
      }

      // Valid pending item
      newItems.push({
        id: Math.random().toString(36).substring(2, 9),
        file: f,
        name: f.name,
        size: f.size,
        status: 'pending',
      });
    }

    setItems((prev) => [...prev, ...newItems]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleRemove = (id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  const handleClearAll = () => {
    setItems([]);
    setBatchError(null);
    setBatchSuccess(null);
  };

  const handleRetry = async (itemId: string) => {
    const target = items.find((i) => i.id === itemId);
    if (!target || isUploading) return;

    setItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, status: 'uploading', error: undefined } : i))
    );

    try {
      const result = await resumesApi.uploadSingleResume(target.file, (percent) => {
        setItems((prev) =>
          prev.map((i) => (i.id === itemId ? { ...i, progress: percent } : i))
        );
      });

      const isCompleted = result.processing_status === 'completed' || result.status === 'completed';
      setItems((prev) =>
        prev.map((i) =>
          i.id === itemId
            ? {
                ...i,
                status: isCompleted ? 'completed' : 'failed',
                error: isCompleted ? undefined : (result.error_message || result.message || 'Processing failed'),
                resumeData: result,
              }
            : i
        )
      );
    } catch (err: any) {
      setItems((prev) =>
        prev.map((i) =>
          i.id === itemId
            ? { ...i, status: 'failed', error: formatApiError(err, 'Upload failed') }
            : i
        )
      );
    }
  };

  const handleRetryAllFailed = async () => {
    const failedItems = items.filter((i) => i.status === 'failed' && i.file.size > 0);
    if (failedItems.length === 0 || isUploading) return;

    // Reset status to pending and run batch upload
    setItems((prev) =>
      prev.map((i) => (i.status === 'failed' && i.file.size > 0 ? { ...i, status: 'pending', error: undefined } : i))
    );
    setTimeout(() => {
      startUpload();
    }, 50);
  };

  const startUpload = async () => {
    const pendingItems = items.filter((i) => i.status === 'pending');
    if (pendingItems.length === 0 || isUploading) return;

    setIsUploading(true);
    setBatchError(null);
    setBatchSuccess(null);
    setUploadProgress(0);

    // Mark pending items as 'uploading'
    setItems((prev) =>
      prev.map((item) =>
        item.status === 'pending' ? { ...item, status: 'uploading', progress: 0 } : item
      )
    );

    try {
      const filesToUpload = pendingItems.map((i) => i.file);

      // Perform upload with upload progress reporting
      const results = await resumesApi.uploadResumes(filesToUpload, (percent) => {
        setUploadProgress(percent);
        if (percent === 100) {
          // Transition to processing state
          setItems((prev) =>
            prev.map((item) =>
              item.status === 'uploading' ? { ...item, status: 'processing' } : item
            )
          );
        }
      });

      // Map results back to items by matching filename & order
      const safeResults = Array.isArray(results) ? results : (results ? [results] : []);
      setItems((prev) => {
        let resultIdx = 0;
        return prev.map((item) => {
          if (item.status === 'uploading' || item.status === 'processing') {
            const resData = safeResults[resultIdx++];
            if (resData) {
              const isSuccess =
                resData.processing_status === 'completed' || resData.status === 'completed';
              return {
                ...item,
                status: isSuccess ? 'completed' : 'failed',
                error: isSuccess ? undefined : (resData.error_message || resData.message || 'Processing failed'),
                resumeData: resData,
              };
            }
            return item;
          }
          return item;
        });
      });

      const succeededCount = safeResults.filter(
        (r) => r.processing_status === 'completed' || r.status === 'completed'
      ).length;
      const failedCountInBatch = safeResults.length - succeededCount;

      if (failedCountInBatch === 0) {
        setBatchSuccess(`Batch complete: All ${succeededCount} candidate resumes processed and indexed successfully.`);
      } else if (succeededCount > 0) {
        setBatchSuccess(`Batch partial: ${succeededCount} resumes completed, ${failedCountInBatch} failed. You can inspect errors or retry.`);
      } else {
        setBatchError('All files in the upload batch encountered errors. Please see individual details below.');
      }
    } catch (err: any) {
      setBatchError(formatApiError(err, 'Bulk resume upload encountered an issue.'));
      // Only set items that were uploading/processing to failed, preserve completed ones!
      setItems((prev) =>
        prev.map((item) =>
          item.status === 'uploading' || item.status === 'processing'
            ? { ...item, status: 'failed', error: 'Network error during upload' }
            : item
        )
      );
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const completedCount = items.filter((i) => i.status === 'completed').length;
  const failedCount = items.filter((i) => i.status === 'failed').length;
  const pendingCount = items.filter((i) => i.status === 'pending').length;
  const inFlightCount = items.filter((i) => i.status === 'uploading' || i.status === 'processing').length;
  const progressPercent = items.length > 0 ? Math.round((completedCount / items.length) * 100) : 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Bulk Resume Upload</h1>
          <p className="text-xs text-slate-500 mt-1">
            Simultaneously upload 10–50 candidate resumes (.PDF, .DOCX, .TXT) with automated NLP parsing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleLoadSampleBatch}
            disabled={loadingSamples || isUploading}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border border-blue-200 bg-blue-50 text-blue-700 text-xs font-bold hover:bg-blue-100 transition-colors shadow-sm disabled:opacity-50 shrink-0 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{loadingSamples ? 'Ingesting 15 Samples...' : 'Load 15 Demo Resumes'}</span>
          </button>

          {completedCount > 0 && (
            <button
              onClick={handleContinueToMatching}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-500/25 transition-all shrink-0 cursor-pointer animate-pulse"
            >
              <Cpu className="w-4 h-4" />
              <span>Continue to AI Matching ({completedCount})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {isOffline && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="font-medium">
              Backend API is currently unreachable. Operating in preview mode.
            </span>
          </div>
          <button
            onClick={() => checkBackendHealth()}
            className="px-3 py-1 rounded-lg bg-amber-200 text-amber-900 font-semibold hover:bg-amber-300 transition-colors cursor-pointer"
          >
            Retry Server Connection
          </button>
        </div>
      )}

      {batchError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-medium">{typeof batchError === 'string' ? batchError : formatApiError(batchError)}</span>
          </div>
          <button onClick={() => setBatchError(null)} className="cursor-pointer">
            <X className="w-4 h-4 text-rose-400 hover:text-rose-600" />
          </button>
        </div>
      )}

      {batchSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{batchSuccess}</span>
          </div>
          <button onClick={() => setBatchSuccess(null)} className="cursor-pointer">
            <X className="w-4 h-4 text-emerald-400 hover:text-emerald-600" />
          </button>
        </div>
      )}

      {/* ── Drag & Drop Zone ────────────────────────────────────── */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl p-10 text-center transition-all ${
          isUploading
            ? 'border-slate-200 bg-slate-50/50 cursor-not-allowed opacity-60'
            : dragActive
            ? 'border-blue-600 bg-blue-50/70 scale-[0.99] cursor-pointer'
            : 'border-slate-300 bg-white hover:border-blue-400 hover:bg-slate-50/50 cursor-pointer'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt"
          disabled={isUploading}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />

        <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 shadow-sm border border-blue-100">
          <UploadCloud className="w-8 h-8" />
        </div>

        <h3 className="text-base font-bold text-slate-900">
          Drag & Drop Candidate Resumes Here
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Upload 10 to 50 resumes at once. Supports PDF, DOCX, and TXT files up to 15MB each.
        </p>

        <div className="flex items-center justify-center gap-3 mt-4 text-[11px] font-semibold text-slate-400">
          <span className="px-2 py-1 bg-slate-100 rounded-lg">.PDF</span>
          <span className="px-2 py-1 bg-slate-100 rounded-lg">.DOCX</span>
          <span className="px-2 py-1 bg-slate-100 rounded-lg">.TXT</span>
          <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-lg font-medium">Max 15MB/file</span>
        </div>
      </div>

      {/* ── Batch Queue & Status ────────────────────────────────── */}
      {items.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Upload Batch Queue ({items.length} files)
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5 flex-wrap">
                <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                  <CheckCircle2 className="w-3 h-3" /> {completedCount} Completed
                </span>
                <span>•</span>
                <span className="inline-flex items-center gap-1 text-rose-600 font-semibold">
                  <AlertCircle className="w-3 h-3" /> {failedCount} Failed
                </span>
                <span>•</span>
                <span className="inline-flex items-center gap-1 text-slate-500 font-medium">
                  <Clock className="w-3 h-3" /> {pendingCount + inFlightCount} Pending
                </span>
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {failedCount > 0 && (
                <button
                  onClick={handleRetryAllFailed}
                  disabled={isUploading}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-xs font-semibold hover:bg-rose-100 disabled:opacity-50 cursor-pointer transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Retry Failed ({failedCount})</span>
                </button>
              )}

              <button
                onClick={handleClearAll}
                disabled={isUploading}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-xs font-medium hover:bg-slate-50 disabled:opacity-50 cursor-pointer transition-colors"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear Queue</span>
              </button>

              {completedCount > 0 && !isUploading && (
                <button
                  onClick={handleContinueToMatching}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-500/25 transition-all cursor-pointer"
                >
                  <Cpu className="w-3.5 h-3.5" />
                  <span>Continue to AI Matching ({completedCount})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}

              <button
                onClick={startUpload}
                disabled={isUploading || pendingCount === 0}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-white text-xs font-semibold shadow-md transition-all cursor-pointer ${
                  pendingCount > 0 && !isUploading
                    ? 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/30 ring-2 ring-blue-400/50'
                    : 'bg-blue-600 hover:bg-blue-700 disabled:opacity-50 shadow-blue-500/20'
                }`}
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing Batch...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Start Batch Extraction {pendingCount > 0 ? `(${pendingCount})` : ''}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Success Banner when resumes are processed */}
          {completedCount > 0 && !isUploading && (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm animate-in fade-in">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-md shadow-emerald-500/20">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-emerald-950">
                    {completedCount} Resumes Ready for AI Matching
                  </h4>
                  <p className="text-[11px] text-emerald-700 mt-0.5">
                    Profiles, skill vectors, and timelines are parsed and indexed. Click below to continue directly to AI matching.
                  </p>
                </div>
              </div>
              <button
                onClick={handleContinueToMatching}
                className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-500/20 transition-all cursor-pointer shrink-0"
              >
                <span>Continue to AI Matching</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}


          {/* Overall Batch Progress */}
          {isUploading && (
            <div className="space-y-1.5 p-3 rounded-xl bg-blue-50/60 border border-blue-100">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span className="flex items-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                  <span>
                    {uploadProgress < 100
                      ? `Uploading files to server (${uploadProgress}%)...`
                      : 'Running NLP semantic extraction & database indexing...'}
                  </span>
                </span>
                <span className="font-bold text-blue-700">
                  {uploadProgress < 100 ? `${uploadProgress}%` : `${progressPercent}%`}
                </span>
              </div>
              <div className="w-full bg-blue-100 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-blue-600 h-2 transition-all duration-300"
                  style={{ width: `${uploadProgress < 100 ? uploadProgress : Math.max(progressPercent, 50)}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Individual File Items */}
          <div className="max-h-96 overflow-y-auto space-y-2 pr-1 divide-y divide-slate-100">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs transition-colors hover:bg-slate-100/60"
              >
                <div className="flex items-center gap-3 min-w-0 pr-2">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                    item.status === 'completed'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                      : item.status === 'failed'
                      ? 'bg-rose-50 border-rose-200 text-rose-600'
                      : 'bg-white border-slate-200 text-slate-600'
                  }`}>
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="font-semibold text-slate-900 truncate" title={item.name}>
                      {item.name}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                      <span>{(item.size / 1024).toFixed(1)} KB</span>
                      {item.error && (
                        <span className="text-rose-600 font-medium truncate max-w-md" title={typeof item.error === 'string' ? item.error : formatApiError(item.error)}>
                          • {typeof item.error === 'string' ? item.error : formatApiError(item.error)}
                        </span>
                      )}
                      {item.status === 'completed' && item.resumeData?.candidate_id && (
                        <span className="text-emerald-700 font-medium">
                          • Candidate indexed
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  {/* Status Badges */}
                  {item.status === 'pending' && (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-slate-200 text-slate-600 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Pending
                    </span>
                  )}
                  {item.status === 'uploading' && (
                    <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      Uploading {item.progress ? `${item.progress}%` : ''}
                    </span>
                  )}
                  {item.status === 'processing' && (
                    <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 text-indigo-700">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      Processing...
                    </span>
                  )}
                  {item.status === 'completed' && (
                    <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-emerald-100 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" />
                      Completed
                    </span>
                  )}
                  {item.status === 'failed' && (
                    <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-rose-100 text-rose-700 border border-rose-200">
                      <AlertCircle className="w-3 h-3" />
                      Failed
                    </span>
                  )}

                  {/* Actions: Process (for pending), Retry (for failed) and Remove */}
                  {item.status === 'pending' && !isUploading && (
                    <button
                      onClick={() => handleRetry(item.id)}
                      title="Upload and parse this resume immediately"
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-[11px] border border-blue-200 transition-colors cursor-pointer shrink-0"
                    >
                      <Sparkles className="w-3 h-3 text-blue-600" />
                      <span>Process</span>
                    </button>
                  )}

                  {item.status === 'failed' && item.file.size > 0 && !isUploading && (
                    <button
                      onClick={() => handleRetry(item.id)}
                      title="Retry this file"
                      className="p-1 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-white border border-transparent hover:border-slate-200 transition-colors cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                  )}

                  {!isUploading && (
                    <button
                      onClick={() => handleRemove(item.id)}
                      title="Remove file"
                      className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-white border border-transparent hover:border-slate-200 transition-colors cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
