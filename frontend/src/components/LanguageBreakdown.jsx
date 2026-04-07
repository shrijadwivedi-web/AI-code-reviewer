import { motion } from 'framer-motion';
import { Code2 } from 'lucide-react';

const LANGUAGE_COLORS = {
  python: 'bg-blue-500',
  javascript: 'bg-yellow-400',
  typescript: 'bg-blue-400',
  go: 'bg-cyan-500',
  java: 'bg-red-500',
  ruby: 'bg-red-600',
  rust: 'bg-orange-500',
  c: 'bg-slate-500',
  cpp: 'bg-indigo-500',
  html: 'bg-orange-600',
  css: 'bg-indigo-400',
  markdown: 'bg-slate-400',
  unknown: 'bg-slate-600',
};

const LanguageBreakdown = ({ stats }) => {
  if (!stats || stats.length === 0) return null;

  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/5">
      <h3 className="text-lg font-semibold text-slate-200 mb-5 flex items-center gap-2">
        <Code2 className="w-5 h-5 text-slate-400" />
        Repository Contents
      </h3>
      
      {/* Segmented Bar */}
      <div className="w-full h-3 bg-dark-800 rounded-full flex overflow-hidden mb-6 shadow-inner ring-1 ring-white/5">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.language}
            initial={{ width: 0 }}
            animate={{ width: `${stat.percentage}%` }}
            transition={{ duration: 1, delay: idx * 0.1, ease: 'easeOut' }}
            className={`h-full ${LANGUAGE_COLORS[stat.language.toLowerCase()] || LANGUAGE_COLORS.unknown}`}
            title={`${stat.language}: ${stat.percentage}%`}
          />
        ))}
      </div>

      {/* Legend Grid */}
      <div className="grid grid-cols-2 gap-y-3 gap-x-4">
        {stats.map((stat) => (
          <div key={stat.language} className="flex items-center justify-between text-sm group">
            <div className="flex items-center gap-2 truncate">
              <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${LANGUAGE_COLORS[stat.language.toLowerCase()] || LANGUAGE_COLORS.unknown}`} />
              <span className="text-slate-300 capitalize truncate group-hover:text-slate-100 transition-colors">
                {stat.language}
              </span>
            </div>
            <span className="text-slate-500 font-mono text-xs">{stat.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LanguageBreakdown;
