import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Users,
  Sparkles,
  Trophy,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Upload,
  X,
  FileText,
  Sliders,
  Search,
  LayoutGrid,
  Table as TableIcon,
  GitCompare,
  ChevronDown,
  ChevronUp,
  Star,
  Loader2,
  RotateCcw
} from 'lucide-react';
import { jobsApi, candidatesApi, matchingApi, shortlistApi } from '../services/api';
import type { Job, Candidate, MatchingAnalysis } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';
import { formatApiError } from '../utils/errors';

// Default standard requisitions ensuring immediate selection availability
const DEFAULT_REQUISITIONS: Job[] = [
  {
    id: '00000000-0000-0000-0000-000000000101',
    title: 'AI Engineer',
    company: 'AVOM Consultants',
    location: 'Remote (US / Global)',
    employment_type: 'Full-time',
    min_experience: 3.0,
    education_req: "Bachelor's Degree in Computer Science or AI",
    description: 'Design, develop, and integrate AI agentic workflows, LLM applications, RAG pipelines, and vector database architectures. Strong expertise in Python, OpenAI/Gemini/Anthropic APIs, LangChain or LlamaIndex, prompt engineering, and evaluation benchmarks.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000102',
    title: 'ML Engineer',
    company: 'Cognitive Systems Labs',
    location: 'San Francisco, CA / Hybrid',
    employment_type: 'Full-time',
    min_experience: 4.0,
    education_req: "Master's Degree in Data Science or Machine Learning",
    description: 'Develop and deploy scalable machine learning models, feature engineering pipelines, and statistical learning algorithms. In-depth understanding of PyTorch, Scikit-learn, Hugging Face, model quantization, and production inference serving.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000103',
    title: 'Software Engineer',
    company: 'Enterprise Cloud Systems',
    location: 'Austin, TX / Remote',
    employment_type: 'Full-time',
    min_experience: 3.0,
    education_req: "Bachelor's Degree in Computer Science or Software Engineering",
    description: 'Build high-throughput backend microservices, robust REST APIs, and event-driven architectures. Strong foundations in data structures, algorithms, object-oriented design, relational databases, unit testing, and clean code principles.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000104',
    title: 'DevOps Engineer',
    company: 'CloudNative Operations',
    location: 'Seattle, WA / Remote',
    employment_type: 'Full-time',
    min_experience: 4.0,
    education_req: "Bachelor's Degree in IT, Systems, or equivalent experience",
    description: 'Architect and manage automated CI/CD deployment pipelines, Kubernetes container orchestration, cloud infrastructure as code (Terraform), system observability, and zero-downtime releases on AWS/GCP.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000105',
    title: 'Cybersecurity Engineer',
    company: 'SecureNet Defense Labs',
    location: 'Washington, DC / Hybrid',
    employment_type: 'Full-time',
    min_experience: 4.0,
    education_req: "Bachelor's Degree in Cybersecurity or Information Assurance",
    description: 'Lead proactive application and network vulnerability assessments, penetration testing, security architecture reviews, IAM policy enforcement, encryption protocols, and incident response procedures.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000106',
    title: 'Full Stack Engineer',
    company: 'AVOM Consultants',
    location: 'Remote (US / Global)',
    employment_type: 'Full-time',
    min_experience: 4.0,
    education_req: "Bachelor's Degree in Computer Science or related",
    description: 'Architect and implement full-stack web applications from responsive modern React/TypeScript user interfaces to scalable Python FastAPI REST microservices, database schemas, and cloud deployments.',
    extracted_requirements: null,
    status: 'active',
    created_at: new Date().toISOString(),
  },
];

export const MatchingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const initialJobId = searchParams.get('job_id') || '';

  // Data states
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(initialJobId);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState<boolean>(true);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [matching, setMatching] = useState(false);
  const [matchingStatusText, setMatchingStatusText] = useState('Computing Semantic Vectors & Scoring...');
  const [results, setResults] = useState<MatchingAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);

  // Shortlisting map (candidate_id -> boolean)
  const [shortlistedMap, setShortlistedMap] = useState<Record<string, boolean>>({});
  const [shortlistLoadingId, setShortlistLoadingId] = useState<string | null>(null);

  // Comparison selection
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Upload handoff state
  const [fromUploadSuccess, setFromUploadSuccess] = useState<boolean>(false);
  const [uploadedResumeCount, setUploadedResumeCount] = useState<number>(0);

  // Candidate pool filters
  const [candidatePoolTab, setCandidatePoolTab] = useState<'all' | 'recent'>('all');
  const [recentCandidateIds, setRecentCandidateIds] = useState<string[]>([]);
  const [candidatePoolSearch, setCandidatePoolSearch] = useState('');

  // Results display filters
  const [resultsSearch, setResultsSearch] = useState('');
  const [tierFilter, setTierFilter] = useState<'all' | 'top' | 'strong' | 'moderate' | 'low'>('all');
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'score' | 'tech' | 'semantic' | 'exp' | 'edu'>('score');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  // Configurable scoring weights
  const [weightsOpen, setWeightsOpen] = useState(false);
  const [weightsPreset, setWeightsPreset] = useState<'balanced' | 'skills' | 'experience' | 'custom'>('balanced');
  const [weights, setWeights] = useState({
    required_skills: 40,
    semantic: 30,
    experience: 20,
    education: 10,
  });

  // Target Job Description Input States
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pastedText, setPastedText] = useState<string>('');
  const [parsing, setParsing] = useState<boolean>(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<'dropdown' | 'upload' | 'paste'>('dropdown');
  const lastAppliedTextRef = useRef<string>('');

  // Initial Fetch & Upload Handoff Handling
  const fetchData = async () => {
    setError(null);
    setCandidatesError(null);
    setCandidatesLoading(true);
    try {
      const [jobsRes, candsRes] = await Promise.all([
        jobsApi.getJobs({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
        candidatesApi.getCandidates({ limit: 100 }).catch((err) => {
          console.error('Failed to get candidates:', err);
          setCandidatesError(formatApiError(err, 'Could not load candidates from server.'));
          return { items: [], total: 0 };
        }),
      ]);
      const fetchedJobs = jobsRes?.items ?? [];
      // Merge fetched jobs with default requisitions to ensure all requested roles exist
      const existingTitles = new Set(fetchedJobs.map((j) => j.title.toLowerCase()));
      const missingDefaults = DEFAULT_REQUISITIONS.filter((dj) => !existingTitles.has(dj.title.toLowerCase()));
      const jobItems = [...fetchedJobs, ...missingDefaults];

      let candItems = candsRes?.items ?? [];

      // Check if navigated from Resume Upload with specific candidate IDs
      const navState = location.state as {
        candidateIds?: string[];
        uploadedMeta?: Array<{ id: string; name: string; filename: string }>;
        fromUpload?: boolean;
        count?: number;
      } | null;

      if (navState && navState.fromUpload && navState.candidateIds && navState.candidateIds.length > 0) {
        setRecentCandidateIds(navState.candidateIds);
        const presentIds = new Set(candItems.map((c) => c.id));
        const missingCandidateIds = navState.candidateIds.filter((id) => !presentIds.has(id));

        if (missingCandidateIds.length > 0) {
          // Attempt to fetch each missing candidate directly from database
          try {
            const fetchedExtras = await Promise.all(
              missingCandidateIds.map((id) => candidatesApi.getCandidate(id).catch(() => null))
            );
            const validExtras = fetchedExtras.filter(Boolean) as Candidate[];
            if (validExtras.length > 0) {
              candItems = [...validExtras, ...candItems];
            } else {
              const missingName =
                navState.uploadedMeta?.[0]?.name ||
                navState.uploadedMeta?.[0]?.filename ||
                missingCandidateIds[0];
              setCandidatesError(
                `Uploaded candidate "${missingName}" was not found in the database. In serverless deployments with SQLite, uploaded data is saved to /tmp and does not persist across separate container invocations. Please configure PostgreSQL DATABASE_URL to persist uploads.`
              );
            }
          } catch {
            const missingName =
              navState.uploadedMeta?.[0]?.name ||
              navState.uploadedMeta?.[0]?.filename ||
              missingCandidateIds[0];
            setCandidatesError(
              `Uploaded candidate "${missingName}" was not found in the database. In serverless deployments with SQLite, uploaded data is saved to /tmp and does not persist across separate container invocations. Please configure PostgreSQL DATABASE_URL to persist uploads.`
            );
          }
        }

        const validSelectedIds = navState.candidateIds.filter((id) =>
          candItems.some((c) => c.id === id)
        );
        setSelectedCandidateIds(validSelectedIds);
        setFromUploadSuccess(true);
        setUploadedResumeCount(navState.count || navState.candidateIds.length);
        setCandidatePoolTab('recent');
      } else {
        // Pre-select all candidate IDs by default
        setSelectedCandidateIds(candItems.map((c) => c.id));
      }

      setJobs(jobItems);
      setCandidates(candItems);

      // Auto select first job if none chosen
      const activeJobId = initialJobId || (jobItems.length > 0 ? jobItems[0].id : '');
      setSelectedJobId(activeJobId);

      // Fetch existing shortlisted candidates for the job if selected
      if (activeJobId) {
        try {
          const shortlists = await shortlistApi.getJobShortlist(activeJobId);
          const sMap: Record<string, boolean> = {};
          (Array.isArray(shortlists) ? shortlists : []).forEach((s) => {
            sMap[s.candidate_id] = true;
          });
          setShortlistedMap(sMap);
        } catch {
          // ignore
        }

        // Fetch existing rankings
        try {
          const matchRes = await matchingApi.getRankings(activeJobId);
          setResults(Array.isArray(matchRes) ? matchRes : []);
        } catch {
          setResults([]);
        }
      }
    } catch (e) {
      console.error(e);
      setError(formatApiError(e, 'Failed to connect to the backend API.'));
      setJobs(DEFAULT_REQUISITIONS);
      setCandidates([]);
      setCandidatesError('Could not load candidates. Please check backend connection and retry.');
      setResults([]);
    } finally {
      setCandidatesLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [initialJobId, location.state]);

  const handleJobChange = async (jobId: string) => {
    setSelectedJobId(jobId);
    setError(null);
    setSelectedForCompare([]);
    try {
      const [matchRes, shortlists] = await Promise.all([
        matchingApi.getRankings(jobId).catch(() => []),
        shortlistApi.getJobShortlist(jobId).catch(() => []),
      ]);
      setResults(Array.isArray(matchRes) ? matchRes : []);
      const sMap: Record<string, boolean> = {};
      (Array.isArray(shortlists) ? shortlists : []).forEach((s) => {
        sMap[s.candidate_id] = true;
      });
      setShortlistedMap(sMap);
    } catch {
      setResults([]);
    }
  };

  const handleDropdownChange = (jobId: string) => {
    setActiveSource('dropdown');
    setUploadedFile(null);
    setPastedText('');
    lastAppliedTextRef.current = '';
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    handleJobChange(jobId);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setParseError(null);

    const validExtensions = ['.pdf', '.docx', '.txt'];
    const lowerName = file.name.toLowerCase();
    const isSupported = validExtensions.some((ext) => lowerName.endsWith(ext));
    if (!isSupported) {
      setUploadError('Unsupported file type. Please upload a .pdf, .docx, or .txt file.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
    if (file.size > MAX_SIZE) {
      setUploadError('File size exceeds the 5 MB limit.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setActiveSource('upload');
    setUploadedFile(file);
    setPastedText('');
    lastAppliedTextRef.current = '';

    setParsing(true);
    try {
      const parsed = await jobsApi.uploadJDDocument(file);
      const newJob = await jobsApi.createJob({
        title: parsed.title || 'Custom Job Description',
        company: parsed.company || 'Custom Upload',
        location: parsed.location || 'Remote',
        employment_type: parsed.employment_type || 'Full-time',
        min_experience: parsed.min_experience !== undefined ? parsed.min_experience : 3.0,
        education_req: parsed.education_req || "Bachelor's Degree",
        description: parsed.description,
      });

      setJobs((prev) => [newJob, ...prev.filter((j) => j.id !== newJob.id)]);
      setSelectedJobId(newJob.id);
      setResults([]);
    } catch (err: any) {
      setParseError(formatApiError(err, 'Failed to parse job description file.'));
    } finally {
      setParsing(false);
    }
  };

  const handleRemoveUploadedFile = () => {
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setActiveSource('dropdown');
    if (jobs.length > 0) {
      const fallbackJob = jobs.find((j) => j.company !== 'Custom' && j.company !== 'Custom Upload' && j.company !== 'Custom Paste') || jobs[0];
      setSelectedJobId(fallbackJob.id);
      handleJobChange(fallbackJob.id);
    }
  };

  const applyPastedText = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || trimmed === lastAppliedTextRef.current.trim()) return;

    if (trimmed.length < 20) {
      setParseError('Please enter at least 20 characters for the job description.');
      return;
    }

    lastAppliedTextRef.current = trimmed;
    setActiveSource('paste');
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';

    setParsing(true);
    try {
      const newJob = await jobsApi.createJob({
        title: 'Custom Job Description',
        company: 'Custom Paste',
        location: 'Remote',
        employment_type: 'Full-time',
        min_experience: 3.0,
        education_req: "Bachelor's Degree",
        description: trimmed,
      });

      setJobs((prev) => [newJob, ...prev.filter((j) => j.id !== newJob.id)]);
      setSelectedJobId(newJob.id);
      setResults([]);
    } catch (err: any) {
      setParseError(formatApiError(err, 'Failed to extract requirements from pasted text.'));
    } finally {
      setParsing(false);
    }
  };

  const handlePasteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setPastedText(text);
    setActiveSource('paste');
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  useEffect(() => {
    if (activeSource !== 'paste' || !pastedText.trim()) return;
    const timer = setTimeout(() => {
      applyPastedText(pastedText);
    }, 600);
    return () => clearTimeout(timer);
  }, [pastedText, activeSource]);

  // Weight Preset Selector
  const applyWeightsPreset = (preset: 'balanced' | 'skills' | 'experience') => {
    setWeightsPreset(preset);
    if (preset === 'balanced') {
      setWeights({ required_skills: 40, semantic: 30, experience: 20, education: 10 });
    } else if (preset === 'skills') {
      setWeights({ required_skills: 50, semantic: 25, experience: 15, education: 10 });
    } else if (preset === 'experience') {
      setWeights({ required_skills: 30, semantic: 20, experience: 40, education: 10 });
    }
  };

  const handleWeightSliderChange = (key: keyof typeof weights, value: number) => {
    setWeightsPreset('custom');
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const totalWeights = useMemo(() => {
    return weights.required_skills + weights.semantic + weights.experience + weights.education;
  }, [weights]);

  const recentCandidatesCount = useMemo(() => {
    return (candidates ?? []).filter((c) => recentCandidateIds.includes(c.id)).length;
  }, [candidates, recentCandidateIds]);

  // Candidate Selection logic
  const filteredCandidatePool = useMemo(() => {
    return (candidates ?? []).filter((c) => {
      if (!c) return false;
      const matchesSearch =
        candidatePoolSearch === '' ||
        (c.name ?? '').toLowerCase().includes(candidatePoolSearch.toLowerCase()) ||
        (c.email && c.email.toLowerCase().includes(candidatePoolSearch.toLowerCase())) ||
        (c.skills && c.skills.some((s) => (s?.skill_name ?? '').toLowerCase().includes(candidatePoolSearch.toLowerCase())));

      if (candidatePoolTab === 'recent') {
        const isRecent = recentCandidateIds.includes(c.id);
        return isRecent && matchesSearch;
      }
      return matchesSearch;
    });
  }, [candidates, candidatePoolSearch, candidatePoolTab, recentCandidateIds]);

  const toggleCandidate = (id: string) => {
    if ((selectedCandidateIds ?? []).includes(id)) {
      setSelectedCandidateIds((selectedCandidateIds ?? []).filter((cId) => cId !== id));
    } else {
      setSelectedCandidateIds([...(selectedCandidateIds ?? []), id]);
    }
  };

  const toggleAllCandidates = () => {
    const candList = candidates ?? [];
    if (selectedCandidateIds.length === candList.length) {
      setSelectedCandidateIds([]);
    } else {
      setSelectedCandidateIds(candList.map((c) => c.id));
    }
  };

  // Run AI Matching
  const handleRunMatching = async () => {
    if (!selectedJobId || selectedCandidateIds.length === 0) return;
    setMatching(true);
    setError(null);
    setMatchingStatusText('Initializing SentenceTransformers vector embedding pipeline...');

    const timer1 = setTimeout(() => {
      setMatchingStatusText('Cross-evaluating candidate skill taxonomy against job criteria...');
    }, 1500);

    const timer2 = setTimeout(() => {
      setMatchingStatusText('Performing interval timeline merging & non-overlapping experience calibration...');
    }, 3500);

    try {
      const analyses = await matchingApi.analyzeMatch(
        selectedJobId,
        selectedCandidateIds,
        weights
      );
      setResults(analyses);
    } catch (err: any) {
      setError(formatApiError(err, 'Semantic matching failed. Check backend server.'));
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setMatching(false);
    }
  };

  // Shortlist Toggle
  const handleToggleShortlist = async (candidateId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!selectedJobId) return;

    setShortlistLoadingId(candidateId);
    const isCurrentlyShortlisted = !!shortlistedMap[candidateId];

    try {
      if (isCurrentlyShortlisted) {
        // Remove from shortlist
        if (selectedJobId) {
          await shortlistApi.removeFromShortlistByJobAndCandidate(selectedJobId, candidateId);
        } else {
          await shortlistApi.removeFromShortlist(candidateId);
        }
        setShortlistedMap((prev) => {
          const next = { ...prev };
          delete next[candidateId];
          return next;
        });
      } else {
        // Add to shortlist
        await shortlistApi.addToShortlist(selectedJobId, candidateId, 'Added from AI Matching Engine');
        setShortlistedMap((prev) => ({ ...prev, [candidateId]: true }));
      }
    } catch {
      // Toggle locally for optimistic UI if api succeeds or graceful fallback
      setShortlistedMap((prev) => ({
        ...prev,
        [candidateId]: !isCurrentlyShortlisted,
      }));
    } finally {
      setShortlistLoadingId(null);
    }
  };

  // Candidate Comparison Toggle
  const handleToggleCompare = (candidateId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (selectedForCompare.includes(candidateId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== candidateId));
    } else {
      if (selectedForCompare.length >= 4) {
        alert('You can compare a maximum of 4 candidates side-by-side.');
        return;
      }
      setSelectedForCompare([...selectedForCompare, candidateId]);
    }
  };

  // Metrics Overview Calculations
  const metrics = useMemo(() => {
    const list = Array.isArray(results) ? results : [];
    if (list.length === 0) return null;
    const total = list.length;
    const top = list.filter((r) => (r?.overall_score ?? 0) >= 80).length;
    const strong = list.filter((r) => (r?.overall_score ?? 0) >= 65 && (r?.overall_score ?? 0) < 80).length;
    const moderate = list.filter((r) => (r?.overall_score ?? 0) >= 50 && (r?.overall_score ?? 0) < 65).length;
    const low = list.filter((r) => (r?.overall_score ?? 0) < 50).length;
    const avg = Math.round(list.reduce((sum, r) => sum + (r?.overall_score ?? 0), 0) / total);
    return { total, top, strong, moderate, low, avg };
  }, [results]);

  // Results Filtering & Sorting
  const processedResults = useMemo(() => {
    let list = Array.isArray(results) ? [...results] : [];

    // Filter by search query
    if (resultsSearch.trim()) {
      const q = resultsSearch.toLowerCase();
      list = list.filter((r) => {
        if (!r) return false;
        const nameMatch = r.candidate?.name?.toLowerCase().includes(q);
        const emailMatch = r.candidate?.email?.toLowerCase().includes(q);
        const skillMatch =
          r.matched_skills?.some((s: any) =>
            (typeof s === 'string' ? s : s?.skill || '').toLowerCase().includes(q)
          ) || false;
        return nameMatch || emailMatch || skillMatch;
      });
    }

    // Filter by tier
    if (tierFilter === 'top') {
      list = list.filter((r) => (r?.overall_score ?? 0) >= 80);
    } else if (tierFilter === 'strong') {
      list = list.filter((r) => (r?.overall_score ?? 0) >= 65 && (r?.overall_score ?? 0) < 80);
    } else if (tierFilter === 'moderate') {
      list = list.filter((r) => (r?.overall_score ?? 0) >= 50 && (r?.overall_score ?? 0) < 65);
    } else if (tierFilter === 'low') {
      list = list.filter((r) => (r?.overall_score ?? 0) < 50);
    }

    // Filter by minimum score
    if (minScoreFilter > 0) {
      list = list.filter((r) => (r?.overall_score ?? 0) >= minScoreFilter);
    }

    // Sort
    list.sort((a, b) => {
      const aTech = a?.technical_score ?? 0;
      const bTech = b?.technical_score ?? 0;
      const aSem = a?.semantic_score ?? 0;
      const bSem = b?.semantic_score ?? 0;
      const aExp = a?.experience_score ?? 0;
      const bExp = b?.experience_score ?? 0;
      const aEdu = a?.education_score ?? 0;
      const bEdu = b?.education_score ?? 0;
      const aOverall = a?.overall_score ?? 0;
      const bOverall = b?.overall_score ?? 0;

      if (sortBy === 'tech') return bTech - aTech;
      if (sortBy === 'semantic') return bSem - aSem;
      if (sortBy === 'exp') return bExp - aExp;
      if (sortBy === 'edu') return bEdu - aEdu;
      return bOverall - aOverall;
    });

    return list;
  }, [results, resultsSearch, tierFilter, minScoreFilter, sortBy]);

  const PRIORITY_TITLES = [
    'ai engineer',
    'ml engineer',
    'software engineer',
    'devops engineer',
    'cybersecurity engineer',
    'full stack engineer',
  ];

  const sortedJobs = useMemo(() => {
    const list = [...(jobs ?? [])];
    return list.sort((a, b) => {
      const aTitle = (a.title || '').toLowerCase();
      const bTitle = (b.title || '').toLowerCase();
      const aIdx = PRIORITY_TITLES.findIndex((p) => aTitle.includes(p));
      const bIdx = PRIORITY_TITLES.findIndex((p) => bTitle.includes(p));
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
      if (aIdx !== -1) return -1;
      if (bIdx !== -1) return 1;
      return aTitle.localeCompare(bTitle);
    });
  }, [jobs]);

  const currentJob = (jobs ?? []).find((j) => j && j.id === selectedJobId);

  // Candidates for Comparison Modal
  const comparedCandidates = useMemo(() => {
    return (Array.isArray(results) ? results : []).filter((r) => r && selectedForCompare.includes(r.candidate_id));
  }, [results, selectedForCompare]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-24">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            AI Semantic Matching Engine
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
              Deterministic 0 - 100
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Enterprise multi-factor recruitment intelligence powered by SentenceTransformers embeddings, skills taxonomy & explainable timelines.
          </p>
        </div>

        {results.length > 0 && (
          <button
            onClick={() => navigate(`/ranking?job_id=${selectedJobId}`)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 shrink-0 cursor-pointer"
          >
            <Trophy className="w-4 h-4" />
            <span>Open Ranking Leaderboard</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* ── Upload Handoff Notification Banner ──────────────────── */}
      {fromUploadSuccess && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-md shadow-emerald-500/20">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-emerald-950">
                {uploadedResumeCount} Resumes Uploaded & Ready for AI Matching
              </h4>
              <p className="text-[11px] text-emerald-700 mt-0.5">
                Uploaded resumes have been automatically pre-selected in your candidate pool below. Select a target job requisition to start matching.
              </p>
            </div>
          </div>
          <button
            onClick={() => setFromUploadSuccess(false)}
            className="text-xs text-emerald-600 hover:text-emerald-800 font-semibold cursor-pointer shrink-0"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── 3-Column Execution Matrix ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1: Select Target Job */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4 max-h-[760px] overflow-y-auto">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
              1
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Target Job Description
            </h3>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1.5">
              Select Existing Requisition
            </label>
            <select
              value={activeSource === 'dropdown' ? selectedJobId : ''}
              onChange={(e) => handleDropdownChange(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-900 bg-white outline-none focus:border-blue-600"
            >
              {activeSource !== 'dropdown' && (
                <option value="" disabled>
                  Select from configured jobs...
                </option>
              )}
              {sortedJobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.company})
                </option>
              ))}
            </select>
          </div>

          <div className="relative flex items-center justify-center my-1">
            <div className="w-full border-t border-slate-200"></div>
            <span className="absolute bg-white px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              OR UPLOAD / PASTE NEW JD
            </span>
          </div>

          {/* New Input Options: Upload (A) & Paste (B) */}
          <div className="space-y-3">
            <div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,.docx,.txt"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={parsing}
                className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-colors cursor-pointer disabled:opacity-50"
              >
                <Upload className="w-3.5 h-3.5 text-slate-600" />
                <span>Upload JD Document (.pdf, .docx)</span>
              </button>

              {uploadedFile && (
                <div className="flex items-center justify-between p-2 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 mt-1.5">
                  <div className="flex items-center gap-1.5 truncate">
                    <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate font-medium">{uploadedFile.name}</span>
                    <span className="text-[10px] text-blue-500 shrink-0">
                      ({(uploadedFile.size / 1024).toFixed(0)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleRemoveUploadedFile}
                    className="p-1 rounded hover:bg-blue-100 text-blue-600 hover:text-blue-800 transition-colors ml-1 shrink-0 cursor-pointer"
                    title="Remove file"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {uploadError && (
                <p className="text-[11px] text-rose-600 font-medium flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  <span>{uploadError}</span>
                </p>
              )}
            </div>

            <div className="space-y-1">
              <textarea
                rows={4}
                value={pastedText}
                onChange={handlePasteChange}
                placeholder="Or paste job requirements here..."
                className="w-full p-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 resize-y leading-relaxed"
              />
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => applyPastedText(pastedText)}
                  disabled={!pastedText.trim() || parsing || activeSource === 'paste'}
                  className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-600 text-[11px] font-semibold hover:bg-blue-100 disabled:opacity-40 transition-colors cursor-pointer"
                >
                  Apply Description
                </button>
                <span className="text-[10px] text-slate-400 font-medium">
                  {pastedText.length} characters
                </span>
              </div>
            </div>

            {parsing && (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-700 animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600 shrink-0" />
                <span>Extracting requirements & skill taxonomy...</span>
              </div>
            )}

            {parseError && (
              <p className="text-[11px] text-rose-600 font-medium flex items-center gap-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{parseError}</span>
              </p>
            )}
          </div>

          {currentJob && (
            <div className="space-y-3 pt-2">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <p className="font-bold text-slate-900 text-sm">{currentJob.title}</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700">
                    {currentJob.company}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">
                  {currentJob.min_experience} yrs min • {currentJob.location} • {currentJob.education_req}
                </p>
                <p className="text-[11px] text-slate-600 line-clamp-3 leading-relaxed mt-1">
                  {currentJob.description}
                </p>
              </div>

              {/* Requirement Taxonomy: Mandatory vs Preferred */}
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Taxonomic Requirements ({currentJob.requirements?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
                  {currentJob.requirements?.map((r) => (
                    <span
                      key={r.id}
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 ${r.category === 'mandatory'
                          ? 'bg-blue-100 text-blue-700 border border-blue-200'
                          : 'bg-purple-50 text-purple-700 border border-purple-200'
                        }`}
                    >
                      <span>{r.skill_name}</span>
                      <span className="text-[9px] opacity-75">
                        {r.category === 'mandatory' ? '★' : 'opt'}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Step 2: Candidate Selection Pool */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4 max-h-[760px] flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
                2
              </div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Candidate Pool ({candidates.length})
              </h3>
            </div>
            <button
              onClick={toggleAllCandidates}
              className="text-[11px] font-semibold text-blue-600 hover:underline cursor-pointer"
            >
              {selectedCandidateIds.length === candidates.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          {/* Candidate Tabs & Search */}
          <div className="space-y-2">
            <div className="flex gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium">
              <button
                type="button"
                onClick={() => setCandidatePoolTab('all')}
                className={`flex-1 py-1.5 rounded-lg text-center transition-all ${candidatePoolTab === 'all'
                    ? 'bg-white font-bold text-slate-900 shadow-xs'
                    : 'text-slate-500 hover:text-slate-800'
                  }`}
              >
                All ({candidates.length})
              </button>
              <button
                type="button"
                onClick={() => setCandidatePoolTab('recent')}
                className={`flex-1 py-1.5 rounded-lg text-center transition-all flex items-center justify-center gap-1 ${candidatePoolTab === 'recent'
                    ? 'bg-white font-bold text-emerald-700 shadow-xs'
                    : 'text-slate-500 hover:text-slate-800'
                  }`}
              >
                <span>Recently Uploaded ({recentCandidatesCount})</span>
                {fromUploadSuccess && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                )}
              </button>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={candidatePoolSearch}
                onChange={(e) => setCandidatePoolSearch(e.target.value)}
                placeholder="Search candidate by name or skill..."
                className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs bg-slate-50 outline-none focus:bg-white focus:border-blue-600"
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 px-1">
              <span>
                Selected: <strong className="text-slate-900">{selectedCandidateIds.length}</strong> of {candidates.length}
              </span>
              <span className="text-[10px] text-slate-400">
                Filtered: {filteredCandidatePool.length}
              </span>
            </div>
          </div>

          {/* Candidate List */}
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 min-h-[300px]">
            {candidatesLoading ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600 mb-2" />
                <p>Loading candidate pool...</p>
              </div>
            ) : candidatesError ? (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 space-y-2.5 my-2">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-1">
                    <p className="font-bold text-rose-900">Could not load candidates</p>
                    <p className="text-[11px] text-rose-700 leading-relaxed">{candidatesError}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => fetchData()}
                  className="w-full py-1.5 px-3 bg-white border border-rose-300 hover:bg-rose-100/60 text-rose-700 font-bold rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retry Loading Candidates</span>
                </button>
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-xs space-y-2">
                <Users className="w-8 h-8 mx-auto text-slate-300" />
                <p className="font-semibold text-slate-700">No candidates in repository</p>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                  Upload resumes or load the demo candidate pool to start AI matching.
                </p>
                <div className="pt-2 flex items-center justify-center gap-2">
                  <Link
                    to="/resumes"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 transition-colors shadow-xs"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Upload Resumes</span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => fetchData()}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 font-semibold text-xs hover:bg-slate-50 transition-colors cursor-pointer"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>
            ) : filteredCandidatePool.length === 0 ? (
              candidatePoolTab === 'recent' ? (
                <div className="text-center py-10 text-slate-400 text-xs space-y-2">
                  <Users className="w-8 h-8 mx-auto text-slate-300" />
                  <p className="font-semibold text-slate-700">No recently uploaded candidates</p>
                  <p className="text-[11px] text-slate-500">
                    Switch to &quot;All&quot; to see all {candidates.length} candidates in the repository.
                  </p>
                  <button
                    type="button"
                    onClick={() => setCandidatePoolTab('all')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 font-bold text-xs hover:bg-blue-100 transition-colors cursor-pointer"
                  >
                    <span>View All ({candidates.length})</span>
                  </button>
                </div>
              ) : (
                <div className="text-center py-10 text-slate-400 text-xs space-y-2">
                  <Users className="w-8 h-8 mx-auto text-slate-300" />
                  <p className="font-semibold text-slate-700">No candidates match &quot;{candidatePoolSearch}&quot;</p>
                  <button
                    type="button"
                    onClick={() => setCandidatePoolSearch('')}
                    className="text-xs text-blue-600 font-semibold hover:underline cursor-pointer"
                  >
                    Clear Search Filter
                  </button>
                </div>
              )
            ) : (
              filteredCandidatePool.map((c) => {
                const isSelected = selectedCandidateIds.includes(c.id);
                return (
                  <div
                    key={c.id}
                    onClick={() => toggleCandidate(c.id)}
                    className={`p-2.5 rounded-xl border text-xs flex items-center justify-between cursor-pointer transition-colors ${isSelected
                        ? 'border-blue-600 bg-blue-50/50'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => { }}
                        className="rounded border-slate-300 text-blue-600 pointer-events-none"
                      />
                      <div className="truncate">
                        <p className="font-semibold text-slate-900 truncate">{c.name}</p>
                        <p className="text-[10px] text-slate-400">
                          {c.total_experience_years} yrs exp • {c.skills?.length || 0} skills
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 capitalize">
                      {c.status}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Step 3: Run AI Matching Action & Configurable Weights */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between space-y-4 max-h-[760px] overflow-y-auto">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
                  3
                </div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  AI Matching Engine
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setWeightsOpen(!weightsOpen)}
                className="text-xs text-blue-600 font-semibold flex items-center gap-1 hover:underline cursor-pointer"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>{weightsOpen ? 'Close Weights' : 'Scoring Weights'}</span>
                {weightsOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>

            {/* Collapsible Weights Configuration */}
            {weightsOpen && (
              <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-200 my-3 space-y-3 animate-in fade-in text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-[11px] uppercase tracking-wider">
                    Scoring Presets
                  </span>
                  <span className={`text-[11px] font-bold ${totalWeights === 100 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    Sum: {totalWeights}% {totalWeights === 100 ? '✓' : '(Must = 100%)'}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-1">
                  <button
                    type="button"
                    onClick={() => applyWeightsPreset('balanced')}
                    className={`py-1 px-1.5 rounded-lg text-[10px] font-bold transition-all text-center ${weightsPreset === 'balanced'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                  >
                    Balanced (40/30)
                  </button>
                  <button
                    type="button"
                    onClick={() => applyWeightsPreset('skills')}
                    className={`py-1 px-1.5 rounded-lg text-[10px] font-bold transition-all text-center ${weightsPreset === 'skills'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                  >
                    Skills First (50%)
                  </button>
                  <button
                    type="button"
                    onClick={() => applyWeightsPreset('experience')}
                    className={`py-1 px-1.5 rounded-lg text-[10px] font-bold transition-all text-center ${weightsPreset === 'experience'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                  >
                    Exp Heavy (40%)
                  </button>
                </div>

                <div className="space-y-2 pt-1">
                  <div>
                    <div className="flex justify-between text-[11px]">
                      <span className="font-medium text-slate-700">1. Technical Skills</span>
                      <span className="font-bold text-blue-600">{weights.required_skills}%</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={70}
                      value={weights.required_skills}
                      onChange={(e) => handleWeightSliderChange('required_skills', Number(e.target.value))}
                      className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px]">
                      <span className="font-medium text-slate-700">2. Semantic Similarity</span>
                      <span className="font-bold text-blue-600">{weights.semantic}%</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={60}
                      value={weights.semantic}
                      onChange={(e) => handleWeightSliderChange('semantic', Number(e.target.value))}
                      className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px]">
                      <span className="font-medium text-slate-700">3. Relevant Experience</span>
                      <span className="font-bold text-blue-600">{weights.experience}%</span>
                    </div>
                    <input
                      type="range"
                      min={5}
                      max={50}
                      value={weights.experience}
                      onChange={(e) => handleWeightSliderChange('experience', Number(e.target.value))}
                      className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px]">
                      <span className="font-medium text-slate-700">4. Education & Qualifications</span>
                      <span className="font-bold text-blue-600">{weights.education}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={30}
                      value={weights.education}
                      onChange={(e) => handleWeightSliderChange('education', Number(e.target.value))}
                      className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3 mt-3 text-xs text-slate-600">
              <p className="leading-relaxed">
                Executes explainable multi-pillar matching using SentenceTransformers embeddings, taxonomic skill normalization, and chronological non-overlapping timeline verification:
              </p>
              <div className="p-3 bg-slate-50 rounded-xl space-y-1.5 text-[11px] font-medium border border-slate-100">
                <div className="flex justify-between">
                  <span>1. Technical Skill Match</span>
                  <span className="font-bold text-blue-600">{weights.required_skills}% Points</span>
                </div>
                <div className="flex justify-between">
                  <span>2. Semantic Similarity</span>
                  <span className="font-bold text-blue-600">{weights.semantic}% Points</span>
                </div>
                <div className="flex justify-between">
                  <span>3. Relevant Experience</span>
                  <span className="font-bold text-blue-600">{weights.experience}% Points</span>
                </div>
                <div className="flex justify-between">
                  <span>4. Education & Qualifications</span>
                  <span className="font-bold text-blue-600">{weights.education}% Points</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2 pt-4 border-t border-slate-100">
            <button
              onClick={handleRunMatching}
              disabled={matching || !selectedJobId || selectedCandidateIds.length === 0}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold hover:from-blue-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25 disabled:opacity-50 cursor-pointer"
            >
              {matching ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>{matchingStatusText}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run AI Matching ({selectedCandidateIds.length} Candidates)</span>
                </>
              )}
            </button>
            <p className="text-[10px] text-center text-slate-400">
              100% Deterministic, mathematically explainable AI. Zero hallucinated credentials.
            </p>
          </div>
        </div>
      </div>

      {/* ── Section 2: Matching Overview Metrics ─────────────────── */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div
            onClick={() => setTierFilter('all')}
            className={`p-4 bg-white rounded-2xl border cursor-pointer transition-all ${tierFilter === 'all' ? 'border-blue-600 shadow-md ring-2 ring-blue-100' : 'border-slate-200 hover:border-slate-300'
              }`}
          >
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Total Evaluated
            </span>
            <span className="text-xl font-black text-slate-900 mt-1 block">
              {metrics.total}
            </span>
            <span className="text-[10px] text-slate-500">All scored profiles</span>
          </div>

          <div
            onClick={() => setTierFilter('top')}
            className={`p-4 bg-white rounded-2xl border cursor-pointer transition-all ${tierFilter === 'top' ? 'border-emerald-600 shadow-md ring-2 ring-emerald-100' : 'border-slate-200 hover:border-slate-300'
              }`}
          >
            <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">
              Top Matches (≥80%)
            </span>
            <span className="text-xl font-black text-emerald-600 mt-1 block">
              {metrics.top}
            </span>
            <span className="text-[10px] text-slate-500">Immediate shortlist</span>
          </div>

          <div
            onClick={() => setTierFilter('strong')}
            className={`p-4 bg-white rounded-2xl border cursor-pointer transition-all ${tierFilter === 'strong' ? 'border-blue-600 shadow-md ring-2 ring-blue-100' : 'border-slate-200 hover:border-slate-300'
              }`}
          >
            <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">
              Strong (65-79%)
            </span>
            <span className="text-xl font-black text-blue-600 mt-1 block">
              {metrics.strong}
            </span>
            <span className="text-[10px] text-slate-500">High alignment</span>
          </div>

          <div
            onClick={() => setTierFilter('moderate')}
            className={`p-4 bg-white rounded-2xl border cursor-pointer transition-all ${tierFilter === 'moderate' ? 'border-amber-600 shadow-md ring-2 ring-amber-100' : 'border-slate-200 hover:border-slate-300'
              }`}
          >
            <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">
              Moderate (50-64%)
            </span>
            <span className="text-xl font-black text-amber-600 mt-1 block">
              {metrics.moderate}
            </span>
            <span className="text-[10px] text-slate-500">Partial skills</span>
          </div>

          <div
            onClick={() => setTierFilter('low')}
            className={`p-4 bg-white rounded-2xl border cursor-pointer transition-all ${tierFilter === 'low' ? 'border-rose-600 shadow-md ring-2 ring-rose-100' : 'border-slate-200 hover:border-slate-300'
              }`}
          >
            <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider block">
              Low Match (&lt;50%)
            </span>
            <span className="text-xl font-black text-rose-600 mt-1 block">
              {metrics.low}
            </span>
            <span className="text-[10px] text-slate-500">Significant gaps</span>
          </div>

          <div className="p-4 bg-gradient-to-tr from-slate-900 to-slate-800 text-white rounded-2xl border border-slate-700 shadow-sm">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Average Score
            </span>
            <span className="text-xl font-black text-emerald-400 mt-1 block">
              {metrics.avg}%
            </span>
            <span className="text-[10px] text-slate-400">Cohort alignment</span>
          </div>
        </div>
      )}

      {/* ── Section 3: Candidate Results Leaderboard ─────────────── */}
      {results.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  Ranked Matching Results ({processedResults.length} Candidates)
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                  Job: {currentJob?.title || 'Selected Requisition'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Explainable rank order based on technical skills, semantic context, experience, and education.
              </p>
            </div>

            {/* View Mode Toggle & Ranking Button */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs">
                <button
                  type="button"
                  onClick={() => setViewMode('table')}
                  className={`p-1.5 rounded-lg transition-all ${viewMode === 'table' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                    }`}
                  title="Table View"
                >
                  <TableIcon className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('cards')}
                  className={`p-1.5 rounded-lg transition-all ${viewMode === 'cards' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                    }`}
                  title="Card Grid View"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
              </div>

              <button
                onClick={() => navigate(`/ranking?job_id=${selectedJobId}`)}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 px-3 py-1.5 rounded-xl border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                <span>Interactive Board</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Leaderboard Filter Controls Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs">
            <div className="flex items-center gap-2 flex-1 max-w-md">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                value={resultsSearch}
                onChange={(e) => setResultsSearch(e.target.value)}
                placeholder="Search ranked candidates by name or skill..."
                className="w-full bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-xs outline-none focus:border-blue-600"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Sort By:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-white border border-slate-200 text-slate-700 text-xs rounded-lg px-2 py-1 outline-none font-medium"
              >
                <option value="score">Overall Score</option>
                <option value="tech">Technical Skills (40)</option>
                <option value="semantic">Semantic Match (30)</option>
                <option value="exp">Experience (20)</option>
                <option value="edu">Education (10)</option>
              </select>

              {(resultsSearch || tierFilter !== 'all' || minScoreFilter > 0) && (
                <button
                  type="button"
                  onClick={() => {
                    setResultsSearch('');
                    setTierFilter('all');
                    setMinScoreFilter(0);
                  }}
                  className="text-[11px] font-semibold text-rose-600 hover:underline cursor-pointer"
                >
                  Reset Filters
                </button>
              )}
            </div>
          </div>

          {/* TABLE VIEW */}
          {viewMode === 'table' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="p-3 pl-4">Rank</th>
                    <th className="p-3">Candidate</th>
                    <th className="p-3">Overall Score</th>
                    <th className="p-3">Tech (40)</th>
                    <th className="p-3">Semantic (30)</th>
                    <th className="p-3">Exp (20)</th>
                    <th className="p-3">Edu (10)</th>
                    <th className="p-3">Matched Skills</th>
                    <th className="p-3 pr-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {processedResults.map((res, index) => {
                    const isShortlisted = !!shortlistedMap[res.candidate_id];
                    const isCompared = selectedForCompare.includes(res.candidate_id);

                    return (
                      <tr key={res.id} className="hover:bg-slate-50 transition-colors">
                        <td className="p-3 pl-4">
                          <span
                            className={`w-6 h-6 rounded-full inline-flex items-center justify-center font-bold text-xs ${index === 0
                                ? 'bg-amber-100 text-amber-700 shadow-xs'
                                : index === 1
                                  ? 'bg-slate-200 text-slate-700'
                                  : index === 2
                                    ? 'bg-amber-50 text-amber-800'
                                    : 'text-slate-400'
                              }`}
                          >
                            {index + 1}
                          </span>
                        </td>
                        <td className="p-3">
                          <p className="font-bold text-slate-900">{res.candidate?.name}</p>
                          <p className="text-[10px] text-slate-400">
                            {res.candidate?.email || 'No email'} • {res.candidate?.total_experience_years} yrs exp
                          </p>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`font-black text-sm ${res.overall_score >= 80
                                  ? 'text-emerald-600'
                                  : res.overall_score >= 65
                                    ? 'text-blue-600'
                                    : res.overall_score >= 50
                                      ? 'text-amber-600'
                                      : 'text-rose-600'
                                }`}
                            >
                              {res.overall_score}%
                            </span>
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${res.overall_score >= 80
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : res.overall_score >= 65
                                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                    : res.overall_score >= 50
                                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                                }`}
                            >
                              {res.overall_score >= 80
                                ? 'Top'
                                : res.overall_score >= 65
                                  ? 'Strong'
                                  : res.overall_score >= 50
                                    ? 'Moderate'
                                    : 'Low'}
                            </span>
                          </div>
                        </td>
                        <td className="p-3 font-semibold text-slate-700">{res.technical_score}</td>
                        <td className="p-3 font-semibold text-slate-700">{res.semantic_score}</td>
                        <td className="p-3 font-semibold text-slate-700">{res.experience_score}</td>
                        <td className="p-3 font-semibold text-slate-700">{res.education_score}</td>
                        <td className="p-3">
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold text-[10px] border border-emerald-200">
                              {res.matched_skills?.length || 0} Aligned
                            </span>
                            {res.missing_skills && res.missing_skills.length > 0 && (
                              <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-medium text-[10px] border border-amber-200">
                                {res.missing_skills.length} Gaps
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 pr-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Compare Checkbox */}
                            <button
                              type="button"
                              onClick={(e) => handleToggleCompare(res.candidate_id, e)}
                              className={`p-1.5 rounded-lg border transition-all text-xs font-medium flex items-center gap-1 cursor-pointer ${isCompared
                                  ? 'bg-purple-100 border-purple-300 text-purple-700'
                                  : 'border-slate-200 text-slate-600 hover:bg-slate-100'
                                }`}
                              title={isCompared ? 'Remove from compare' : 'Select for compare'}
                            >
                              <GitCompare className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">{isCompared ? 'Selected' : 'Compare'}</span>
                            </button>

                            {/* Shortlist Toggle */}
                            <button
                              type="button"
                              onClick={(e) => handleToggleShortlist(res.candidate_id, e)}
                              disabled={shortlistLoadingId === res.candidate_id}
                              className={`p-1.5 rounded-lg border transition-all text-xs font-semibold flex items-center gap-1 cursor-pointer ${isShortlisted
                                  ? 'bg-emerald-600 border-emerald-600 text-white shadow-xs'
                                  : 'border-slate-200 bg-white text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200'
                                }`}
                              title={isShortlisted ? 'Candidate Shortlisted' : 'Add to Shortlist'}
                            >
                              <Star className={`w-3.5 h-3.5 ${isShortlisted ? 'fill-current' : ''}`} />
                              <span className="hidden sm:inline">
                                {isShortlisted ? 'Shortlisted' : 'Shortlist'}
                              </span>
                            </button>

                            {/* Inspect Breakdown */}
                            <button
                              onClick={() => setDetailCandidateId(res.candidate_id)}
                              className="px-2.5 py-1.5 rounded-lg bg-blue-50 text-blue-700 font-semibold hover:bg-blue-100 text-xs transition-colors cursor-pointer"
                            >
                              Deep Analysis
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            /* CARD GRID VIEW */
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pt-2">
              {processedResults.map((res, index) => {
                const isShortlisted = !!shortlistedMap[res.candidate_id];
                const isCompared = selectedForCompare.includes(res.candidate_id);

                return (
                  <div
                    key={res.id}
                    className="p-5 rounded-2xl border border-slate-200 bg-white hover:border-blue-300 hover:shadow-md transition-all space-y-4 relative"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs ${index === 0
                              ? 'bg-amber-100 text-amber-700'
                              : index === 1
                                ? 'bg-slate-200 text-slate-700'
                                : index === 2
                                  ? 'bg-amber-50 text-amber-800'
                                  : 'bg-slate-100 text-slate-600'
                            }`}
                        >
                          #{index + 1}
                        </span>
                        <div>
                          <h4 className="font-bold text-slate-900 text-sm">{res.candidate?.name}</h4>
                          <p className="text-[11px] text-slate-400">
                            {res.candidate?.total_experience_years} yrs exp • {res.candidate?.location || 'Remote'}
                          </p>
                        </div>
                      </div>

                      <div className="text-right">
                        <span
                          className={`text-xl font-black ${res.overall_score >= 80
                              ? 'text-emerald-600'
                              : res.overall_score >= 65
                                ? 'text-blue-600'
                                : res.overall_score >= 50
                                  ? 'text-amber-600'
                                  : 'text-rose-600'
                            }`}
                        >
                          {res.overall_score}%
                        </span>
                        <span className="text-[10px] text-slate-400 block uppercase font-bold">
                          {res.overall_score >= 80
                            ? 'Top Match'
                            : res.overall_score >= 65
                              ? 'Strong'
                              : res.overall_score >= 50
                                ? 'Moderate'
                                : 'Low'}
                        </span>
                      </div>
                    </div>

                    {/* 4 Pillars Progress Bar */}
                    <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Tech ({weights.required_skills}%)</span>
                        <span className="font-bold text-slate-900">{res.technical_score} pts</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Semantic ({weights.semantic}%)</span>
                        <span className="font-bold text-slate-900">{res.semantic_score} pts</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Experience ({weights.experience}%)</span>
                        <span className="font-bold text-slate-900">{res.experience_score} pts</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Education ({weights.education}%)</span>
                        <span className="font-bold text-slate-900">{res.education_score} pts</span>
                      </div>
                    </div>

                    {/* Matched & Missing Skills pills */}
                    <div className="space-y-1.5">
                      <div className="flex flex-wrap gap-1">
                        {res.matched_skills?.slice(0, 4).map((s: any, idx: number) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
                          >
                            {typeof s === 'string' ? s : s.skill}
                          </span>
                        ))}
                        {(res.matched_skills?.length || 0) > 4 && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500">
                            +{(res.matched_skills?.length || 0) - 4} more
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={(e) => handleToggleCompare(res.candidate_id, e)}
                          className={`p-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 cursor-pointer ${isCompared
                              ? 'bg-purple-100 border-purple-300 text-purple-700'
                              : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                            }`}
                          title="Compare"
                        >
                          <GitCompare className="w-3.5 h-3.5" />
                        </button>

                        <button
                          type="button"
                          onClick={(e) => handleToggleShortlist(res.candidate_id, e)}
                          className={`p-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 cursor-pointer ${isShortlisted
                              ? 'bg-emerald-600 border-emerald-600 text-white'
                              : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                            }`}
                          title={isShortlisted ? 'Shortlisted' : 'Add to Shortlist'}
                        >
                          <Star className={`w-3.5 h-3.5 ${isShortlisted ? 'fill-current' : ''}`} />
                        </button>
                      </div>

                      <button
                        onClick={() => setDetailCandidateId(res.candidate_id)}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-xs cursor-pointer"
                      >
                        Deep Analysis
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── Section 4: Floating Side-by-Side Comparison Tray ────── */}
      {selectedForCompare.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-4 animate-in slide-in-from-bottom duration-200">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-bold">
              {selectedForCompare.length} Candidates Selected for Comparison
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowComparisonModal(true)}
              className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-md shadow-purple-500/25 cursor-pointer"
            >
              Compare Side-by-Side
            </button>
            <button
              onClick={() => setSelectedForCompare([])}
              className="px-2 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* ── Section 5: Built-in Candidate Comparison Modal ──────── */}
      {showComparisonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <GitCompare className="w-4 h-4 text-purple-600" />
                  <span>Candidate Side-by-Side Comparison Matrix</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Direct evaluation against {currentJob?.title || 'Selected Job'} requirements.
                </p>
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Comparison Grid */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className={`grid grid-cols-1 md:grid-cols-${Math.min(comparedCandidates.length, 4)} gap-4`}>
                {comparedCandidates.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 bg-slate-50/70 border border-slate-200 rounded-2xl space-y-3"
                  >
                    <div>
                      <h4 className="font-bold text-slate-900 text-base">{c.candidate?.name}</h4>
                      <p className="text-xs text-slate-500">{c.candidate?.email}</p>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-slate-100 text-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block">
                        Overall Compatibility
                      </span>
                      <span className={`text-2xl font-black ${c.overall_score >= 80 ? 'text-emerald-600' : c.overall_score >= 65 ? 'text-blue-600' : 'text-amber-600'
                        }`}>
                        {c.overall_score}%
                      </span>
                    </div>

                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between py-1 border-b border-slate-200/60">
                        <span className="text-slate-500">Technical (40):</span>
                        <span className="font-bold text-slate-800">{c.technical_score}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/60">
                        <span className="text-slate-500">Semantic (30):</span>
                        <span className="font-bold text-slate-800">{c.semantic_score}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/60">
                        <span className="text-slate-500">Experience (20):</span>
                        <span className="font-bold text-slate-800">{c.experience_score}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/60">
                        <span className="text-slate-500">Education (10):</span>
                        <span className="font-bold text-slate-800">{c.education_score}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/60">
                        <span className="text-slate-500">Experience Yrs:</span>
                        <span className="font-bold text-slate-800">{c.candidate?.total_experience_years} yrs</span>
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-emerald-700 uppercase block mb-1">
                        Verified Skills ({c.matched_skills?.length || 0}):
                      </span>
                      <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto">
                        {c.matched_skills?.map((s: any, idx: number) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800"
                          >
                            {typeof s === 'string' ? s : s.skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {c.missing_skills && c.missing_skills.length > 0 && (
                      <div>
                        <span className="text-[10px] font-bold text-amber-700 uppercase block mb-1">
                          Missing Skills ({c.missing_skills.length}):
                        </span>
                        <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                          {c.missing_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="pt-2">
                      <button
                        onClick={() => {
                          setShowComparisonModal(false);
                          setDetailCandidateId(c.candidate_id);
                        }}
                        className="w-full py-2 rounded-xl bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition-colors"
                      >
                        Open Full Dossier
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Candidate Deep Analysis Modal */}
      {detailCandidateId && (
        <CandidateDetailModal
          candidateId={detailCandidateId}
          jobId={selectedJobId}
          initialAnalysis={results.find((r) => r.candidate_id === detailCandidateId)}
          initialCandidate={
            candidates.find((c) => c.id === detailCandidateId) ||
            results.find((r) => r.candidate_id === detailCandidateId)?.candidate
          }
          onClose={() => setDetailCandidateId(null)}
        />
      )}
    </div>
  );
};

export const AIMatchingPage = MatchingPage;
export default MatchingPage;
