import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Clock,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  Search,
  Terminal,
  Zap
} from 'lucide-react';
import { agentsApi } from '../services/api';
import type { AgentExecution, AgentActivityStats } from '../types';

export const AgentActivityPage: React.FC = () => {
  const [stats, setStats] = useState<AgentActivityStats | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [agentFilter, setAgentFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selectedExecution, setSelectedExecution] = useState<AgentExecution | null>(null);

  const fetchData = async () => {
    try {
      const [statsData, execData] = await Promise.all([
        agentsApi.getStats(),
        agentsApi.getExecutions({ limit: 100 }),
      ]);
      setStats(statsData);
      setExecutions(execData);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const agentList = [
    'JobDescriptionAgent',
    'ResumeIntelligenceAgent',
    'TechnicalSkillsAgent',
    'ExperienceEvaluationAgent',
    'CandidateMatchingAgent',
    'CandidateComparisonAgent',
    'InterviewIntelligenceAgent',
    'RecruiterCopilotAgent',
  ];

  const filteredExecutions = executions.filter((ex) => {
    const matchAgent = agentFilter === 'all' || ex.agent_name === agentFilter;
    const matchStatus = statusFilter === 'all' || ex.status === statusFilter;
    const matchSearch =
      search === '' ||
      ex.agent_name.toLowerCase().includes(search.toLowerCase()) ||
      (ex.model_name && ex.model_name.toLowerCase().includes(search.toLowerCase())) ||
      (ex.id && ex.id.toLowerCase().includes(search.toLowerCase()));
    return matchAgent && matchStatus && matchSearch;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              Agent Observability & Telemetry
            </h1>
            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time execution latency, token economics, and error tracing across all 8 specialized AI agents.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors shadow-xs shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-blue-600' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Telemetry'}</span>
        </button>
      </div>

      {/* ── KPI Metric Cards ───────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Total Invocations
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {stats ? stats.total_executions.toLocaleString() : '—'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Logged across all active workflows</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Success Reliability
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-emerald-700">
            {stats ? `${stats.success_rate.toFixed(1)}%` : '—'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Zero unhandled agent runtime failures</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Average Latency
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {stats ? `${Math.round(stats.avg_latency_ms)} ms` : '—'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">End-to-end execution and validation</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Tokens Consumed
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {stats ? stats.total_tokens.toLocaleString() : '—'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Prompt and completion tokens</p>
        </div>
      </div>

      {/* ── 8 Specialized Agents Fleet Grid ─────────────────────── */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Specialized Agent Fleet ({agentList.length} Active Agents)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {agentList.map((agentName) => {
            const agentStats = stats?.by_agent?.[agentName] || {
              executions: 0,
              avg_latency_ms: 0,
              success_rate: 100,
              total_tokens: 0,
            };

            return (
              <div
                key={agentName}
                onClick={() => setAgentFilter(agentFilter === agentName ? 'all' : agentName)}
                className={`bg-white p-4 rounded-xl border transition-all cursor-pointer ${
                  agentFilter === agentName
                    ? 'border-blue-600 ring-2 ring-blue-500/20 shadow-sm'
                    : 'border-slate-200/80 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-xs text-slate-900 truncate">
                    {agentName.replace('Agent', '')}
                  </span>
                  <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
                    {agentStats.executions} runs
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                  <div>
                    <span className="block text-slate-400 text-[10px]">Latency</span>
                    <span className="font-semibold text-slate-700">
                      {Math.round(agentStats.avg_latency_ms)} ms
                    </span>
                  </div>
                  <div>
                    <span className="block text-slate-400 text-[10px]">Reliability</span>
                    <span className="font-semibold text-emerald-600">
                      {agentStats.success_rate.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Executions Log Stream ───────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Controls */}
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto flex-1">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by agent name, model, or execution ID..."
              className="text-xs bg-transparent border-none outline-none w-full text-slate-800 placeholder-slate-400"
            />
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <select
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium outline-none"
            >
              <option value="all">All Agents</option>
              {agentList.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Agent Name</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Tokens</th>
                <th className="py-3 px-4">Model Engine</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredExecutions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No matching agent telemetry records found.
                  </td>
                </tr>
              ) : (
                filteredExecutions.slice(0, 50).map((ex) => (
                  <tr key={ex.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                      <Cpu className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      <span>{ex.agent_name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          ex.status === 'success'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {ex.status === 'success' ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <AlertOctagon className="w-3 h-3" />
                        )}
                        <span>{ex.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {Math.round(ex.execution_time_ms)} ms
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {ex.tokens_used ? ex.tokens_used.toLocaleString() : '—'}
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                      {ex.model_name || 'deterministic'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(ex.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedExecution(ex)}
                        className="text-blue-600 hover:text-blue-800 font-semibold"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Inspect Execution Modal ────────────────────────────── */}
      {selectedExecution && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Terminal className="w-4 h-4 text-blue-600" />
                <span>Execution Trace: {selectedExecution.agent_name}</span>
              </h3>
              <button
                onClick={() => setSelectedExecution(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                &times;
              </button>
            </div>

            <div className="space-y-3 mt-4 text-xs">
              <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Execution ID</span>
                  <span className="font-mono text-slate-800">{selectedExecution.id}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Model Engine</span>
                  <span className="font-mono text-slate-800">{selectedExecution.model_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Duration</span>
                  <span className="font-semibold text-slate-800">{selectedExecution.execution_time_ms.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Status</span>
                  <span className="font-semibold uppercase text-emerald-700">{selectedExecution.status}</span>
                </div>
              </div>

              {selectedExecution.error_message && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">
                  <span className="font-bold block mb-1">Error Trace:</span>
                  <p className="font-mono text-[11px]">{selectedExecution.error_message}</p>
                </div>
              )}

              {selectedExecution.metadata_json && (
                <div>
                  <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider block mb-1">
                    Structured Execution Metadata
                  </span>
                  <pre className="p-3 bg-slate-900 text-emerald-400 rounded-xl font-mono text-[11px] overflow-x-auto max-h-60">
                    {JSON.stringify(selectedExecution.metadata_json, null, 2)}
                  </pre>
                </div>
              )}

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedExecution(null)}
                  className="px-4 py-1.5 rounded-xl bg-slate-100 text-slate-700 font-semibold hover:bg-slate-200 text-xs"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
