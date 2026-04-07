import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Github, Key, Search, Sparkles, Loader2, AlertCircle } from 'lucide-react';

const Hero = ({ onAnalyze, isLoading, error }) => {
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    onAnalyze({ url: url.trim(), token: token.trim() });
  };

  return (
    <div className="relative pt-32 pb-20 sm:pt-40 sm:pb-24 overflow-hidden">
      {/* Background glowing blobs */}
      <div className="absolute top-0 left-1/2 w-full -translate-x-1/2 h-[500px] opacity-20 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-500 blur-[120px] rounded-full mix-blend-screen" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 text-brand-400 text-sm font-medium mb-6 border border-brand-500/20">
            <Sparkles className="w-4 h-4" />
            AI-Powered Code Intelligence
          </div>
          <h1 className="text-5xl sm:text-7xl font-bold tracking-tight mb-8">
            Review code at <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 via-emerald-300 to-teal-300">
              superhuman speed.
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            Drop in a GitHub repository or pull request URL. Our static analysis engine and AI models will immediately flag bugs, clean up technical debt, and suggest best practices.
          </p>
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          onSubmit={handleSubmit}
          className="max-w-2xl mx-auto"
        >
          <div className="flex flex-col gap-4">
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-brand-400 transition-colors">
                <Github className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/facebook/react"
                className="block w-full pl-12 pr-4 py-4 bg-dark-800/50 border border-slate-700/50 rounded-2xl text-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition-all shadow-xl backdrop-blur-sm"
                required
              />
            </div>

            <AnimatePresence>
              {showToken && (
                <motion.div
                  initial={{ opacity: 0, height: 0, marginTop: -16 }}
                  animate={{ opacity: 1, height: 'auto', marginTop: 0 }}
                  exit={{ opacity: 0, height: 0, marginTop: -16 }}
                  className="relative overflow-hidden"
                >
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                    <Key className="w-5 h-5" />
                  </div>
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="GitHub Personal Access Token (Optional)"
                    className="block w-full pl-12 pr-4 py-3 bg-dark-800/30 border border-slate-700/50 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition-all font-mono text-sm"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-2">
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2 transition-colors"
              >
                {showToken ? "- Hide Token" : "+ Add GitHub Token (avoids rate limits)"}
              </button>
              <button
                type="submit"
                disabled={isLoading || !url}
                className="w-full sm:w-auto flex items-center outline-none justify-center gap-2 px-8 py-3 bg-brand-500 hover:bg-brand-600 text-dark-950 font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(34,197,94,0.3)] hover:shadow-[0_0_25px_rgba(34,197,94,0.5)] active:scale-95"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing Code...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Start Review Engine
                  </>
                )}
              </button>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-6 flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-left"
              >
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-red-400 font-medium">Analysis Failed</h4>
                  <p className="text-sm text-red-300/80 mt-1">
                    {error?.response?.data?.detail || error.message || 'An unexpected error occurred.'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.form>
      </div>
    </div>
  );
};

export default Hero;
