import { motion } from 'framer-motion';

const ScoreRing = ({ score, summary }) => {
  // Determine colors based on score
  let strokeColor = 'stroke-red-500';
  let glowColor = 'shadow-[0_0_30px_rgba(239,68,68,0.2)]';
  if (score >= 85) {
    strokeColor = 'stroke-emerald-400';
    glowColor = 'shadow-[0_0_30px_rgba(52,211,153,0.3)]';
  } else if (score >= 70) {
    strokeColor = 'stroke-amber-400';
    glowColor = 'shadow-[0_0_30px_rgba(251,191,36,0.2)]';
  }

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`glass-panel p-8 rounded-3xl flex flex-col items-center justify-center relative overflow-hidden group ${glowColor} transition-shadow duration-500`}>
      <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="relative w-40 h-40 flex items-center justify-center mb-6">
        {/* Background circle */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 140 140">
          <circle
            cx="70"
            cy="70"
            r={radius}
            className="stroke-slate-800"
            strokeWidth="8"
            fill="none"
          />
          {/* Animated score circle */}
          <motion.circle
            cx="70"
            cy="70"
            r={radius}
            className={strokeColor}
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
            style={{ strokeDasharray: circumference }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8, duration: 0.5 }}
            className="text-4xl font-bold font-mono text-slate-100 tracking-tighter"
          >
            {score}
          </motion.span>
          <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-1">/ 100</span>
        </div>
      </div>

      <div className="text-center z-10 w-full relative">
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Quality Score</h3>
        <p className="text-sm text-slate-400 leading-relaxed max-w-[250px] mx-auto min-h-[60px]">
          {summary}
        </p>
      </div>
    </div>
  );
};

export default ScoreRing;
