import { motion, AnimatePresence } from 'framer-motion';
import { useAnalysis } from './hooks/useAnalysis';
import Hero from './components/Hero';
import ScoreRing from './components/ScoreRing';
import IssuesList from './components/IssuesList';
import SuggestionsPanel from './components/SuggestionsPanel';
import LanguageBreakdown from './components/LanguageBreakdown';
import { Code2 } from 'lucide-react';

function App() {
  const { mutate: analyze, data, isPending, error } = useAnalysis();

  return (
    <div className="min-h-screen relative font-sans overflow-x-hidden">
      {/* Global Background Grid & Glows */}
      <div className="fixed inset-0 pointer-events-none z-[-1] bg-dark-900 flex justify-center">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute top-0 w-full max-w-7xl h-[600px] bg-brand-900/20 blur-[150px] -translate-y-1/2"></div>
      </div>

      <main className="relative z-10 container mx-auto px-4 pb-24">
        {/* Header simple nav */}
        <nav className="py-6 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-100 font-bold text-xl tracking-tight">
             <div className="p-1.5 bg-brand-500 rounded-lg text-dark-950">
               <Code2 className="w-5 h-5" />
             </div>
             AI Code Reviewer
          </div>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors">
            View on GitHub
          </a>
        </nav>

        <Hero onAnalyze={analyze} isLoading={isPending} error={error} />

        {/* Dashboard Layout */}
        <AnimatePresence mode="wait">
          {data && !isPending && (
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="mt-12 max-w-6xl mx-auto"
            >
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
                
                {/* Left Column: Score & Stats */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                  <ScoreRing score={data.score} summary={data.summary} />
                  <LanguageBreakdown stats={data.language_breakdown} />
                </div>

                {/* Right Column: AI Suggestions & Issues */}
                <div className="lg:col-span-8 flex flex-col gap-6">
                  <SuggestionsPanel suggestions={data.suggestions} />
                  <IssuesList issues={data.issues} />
                </div>
                
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
