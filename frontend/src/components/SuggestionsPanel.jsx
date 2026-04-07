import { motion } from 'framer-motion';
import { Bot, FileCode, CheckCircle2, ChevronRight } from 'lucide-react';

const SuggestionsPanel = ({ suggestions }) => {
  if (!suggestions?.length) {
    return null;
  }

  return (
    <div className="glass-panel rounded-3xl p-6 sm:p-8 relative overflow-hidden group border border-brand-500/20">
      {/* Decorative background glow */}
      <div className="absolute -top-40 -right-40 w-80 h-80 bg-brand-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-brand-500/20 transition-colors duration-700" />

      <h2 className="text-xl font-semibold mb-6 flex items-center gap-3 text-slate-100">
        <div className="p-2 bg-gradient-to-br from-brand-400 to-teal-500 rounded-xl shadow-lg ring-1 ring-white/20">
          <Bot className="w-5 h-5 text-dark-950" />
        </div>
        AI Actions
      </h2>

      <div className="space-y-6 relative z-10">
        {suggestions.map((sugg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
            className="flex items-start gap-4 p-5 rounded-2xl bg-dark-800/40 border border-slate-700/50 hover:bg-dark-800/60 hover:border-brand-500/30 transition-all shadow-sm group/item"
          >
            <div className="mt-1 shrink-0">
              <CheckCircle2 className="w-5 h-5 text-brand-400" />
            </div>
            <div className="flex-1 min-w-0">
              {sugg.file !== 'general' && (
                <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 mb-2 border border-slate-700/50 bg-dark-900/50 inline-flex px-2 py-1 rounded-md">
                  <FileCode className="w-3.5 h-3.5" />
                  <span className="truncate max-w-[200px] sm:max-w-xs block">{sugg.file}</span>
                </div>
              )}
              <p className="text-slate-300 leading-relaxed">
                {sugg.suggestion}
              </p>
              
              {sugg.example && (
                <div className="mt-4 relative">
                  <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-brand-500/30 rounded-full"></div>
                  <pre className="pl-4 py-2 pr-2 overflow-x-auto text-sm font-mono text-emerald-300/90 leading-relaxed scrollbar-thin">
                    <code>{sugg.example}</code>
                  </pre>
                </div>
              )}
            </div>
            <div className="shrink-0 opacity-0 group-hover/item:opacity-100 transition-opacity self-center">
                <ChevronRight className="w-5 h-5 text-brand-500/50" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default SuggestionsPanel;
