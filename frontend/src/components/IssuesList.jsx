import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp, FileCode2 } from 'lucide-react';

const SEVERITY_CONFIG = {
  critical: {
    icon: AlertCircle,
    color: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/20',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/20',
  },
  info: {
    icon: Info,
    color: 'text-blue-400',
    bg: 'bg-blue-400/10',
    border: 'border-blue-400/20',
  },
};

const IssueRow = ({ issue }) => {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[issue.severity];
  const Icon = config.icon;

  return (
    <motion.div
      layout
      className={`border rounded-xl mb-3 overflow-hidden transition-colors ${
        expanded ? 'bg-dark-800/80 border-brand-500/30' : 'bg-dark-800/30 border-slate-700/50 hover:border-slate-600'
      }`}
    >
      <div
        className="px-4 py-4 sm:px-6 cursor-pointer flex items-start gap-4"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`mt-0.5 p-2 rounded-lg shrink-0 ${config.bg} ${config.color}`}>
          <Icon className="w-5 h-5" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${config.bg} ${config.color} border ${config.border}`}>
              {issue.severity}
            </span>
            <span className="text-sm font-mono text-slate-400 truncate flex items-center gap-1.5 bg-dark-900/50 px-2 py-0.5 rounded-md border border-slate-700/50">
              <FileCode2 className="w-3 h-3" />
              {issue.file}{issue.line ? `:${issue.line}` : ''}
            </span>
          </div>
          <h4 className="text-slate-200 font-medium leading-snug">
            {issue.message}
          </h4>
        </div>

        <button className="text-slate-500 hover:text-slate-300 transition-colors mt-1 shrink-0">
          {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-700/50 bg-dark-900/50"
          >
            <div className="px-4 py-4 sm:px-6">
              <div className="text-sm text-slate-400">
                <strong className="text-slate-300">Issue Type:</strong> <code className="font-mono text-brand-300 bg-brand-400/10 px-1.5 py-0.5 rounded ml-1">{issue.type}</code>
              </div>
              {/* Future extension: code preview snippet here */}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const IssuesList = ({ issues }) => {
  const [filter, setFilter] = useState('all');

  const filteredIssues = filter === 'all' 
    ? issues 
    : issues.filter(i => i.severity === filter);

  if (!issues?.length) {
    return (
      <div className="glass-panel p-8 rounded-3xl text-center flex flex-col items-center justify-center h-full min-h-[300px]">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4 border border-emerald-500/20">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-semibold text-slate-200 mb-2">Clean Codebase!</h3>
        <p className="text-slate-400 max-w-sm">No significant issues detected by our static analyzer. Excellent work keeping technical debt low.</p>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-3xl flex flex-col h-[600px] overflow-hidden border border-white/10 relative">
      <div className="px-6 pt-6 pb-4 border-b border-white/10 shrink-0 sticky top-0 bg-dark-900/80 backdrop-blur-xl z-20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            Static Analysis
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-brand-400 border border-slate-700">
              {issues.length} {issues.length === 1 ? 'Issue' : 'Issues'}
            </span>
          </h2>
          
          <div className="flex bg-dark-900 p-1 rounded-xl border border-slate-700/50 shadow-inner">
            {['all', 'critical', 'warning', 'info'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 sm:px-4 py-1.5 rounded-lg text-sm font-medium transition-all capitalize ${
                  filter === f 
                    ? 'bg-slate-700 text-slate-100 shadow' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="p-6 overflow-y-auto flex-1 scroll-smooth">
        <AnimatePresence mode="popLayout">
          {filteredIssues.map((issue, idx) => (
            <motion.div
              layout
              key={`${issue.file}-${issue.line}-${issue.type}-${idx}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2, delay: Math.min(idx * 0.05, 0.3) }}
            >
              <IssueRow issue={issue} />
            </motion.div>
          ))}
          {filteredIssues.length === 0 && (
             <motion.div
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               className="text-center py-12 text-slate-500"
             >
               No {filter} issues found.
             </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Scroll shadow indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-dark-900/80 to-transparent pointer-events-none rounded-b-3xl"></div>
    </div>
  );
};

export default IssuesList;
