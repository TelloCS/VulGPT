import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useScanResults } from '../hooks/useScanResults';
import { useScanStats } from '../hooks/useScanStats'; 
import VulnerabilityCard from './VulnerabilityCard';
import ScanStatsBoard from './ScanStatsBoard'; 
import ExportCsvButton from './ExportCsvButton';
import { Loader2, ArrowLeft, ChevronDown, Clock, CheckCircle } from 'lucide-react';

const ScanReport = () => {
  const { scanId } = useParams();
  const [elapsedTime, setElapsedTime] = useState(0);

  const { data: stats, isLoading: isLoadingStats } = useScanStats(scanId);
  
  const isCompleted = stats?.status === 'COMPLETED';
  const isProcessing = isLoadingStats || !stats || stats.status === 'PROCESSING';

  const { 
    data: vulnData, 
    isLoading: isLoadingVulns, 
    isError, 
    error, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage 
  } = useScanResults(scanId, isCompleted);
  
  const vulnerabilities = vulnData?.pages.flatMap(page => page.items) || [];

  // Determine when to drop the loading veil
  // Keep the loading screen up if we are processing OR if the final list is currently downloading
  const showLoadingScreen = isProcessing || isLoadingVulns;

  // Timer anchored to Neo4j
  useEffect(() => {
    let interval;
    const updateTimer = () => {
      if (!stats?.created_at) return;
      const startTime = stats.created_at; 
      const endTime = stats.completed_at ? stats.completed_at : Date.now();
      setElapsedTime(Math.floor((endTime - startTime) / 1000));
    };

    if (isProcessing) {
      interval = setInterval(updateTimer, 1000);
    } else {
      updateTimer(); // Lock in final time
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isProcessing, stats?.created_at, stats?.completed_at]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  if (isError) {
    return (
      <div className="p-8 max-w-5xl mx-auto text-center text-red-600">
        <p>Error loading scan results: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-200 mb-6 hover:text-purple-300">
        <ArrowLeft className="w-4 h-4" /> Back to Global Dashboard
      </Link>

      <header className="mb-6 p-6 bg-[#262632] from-slate-900 to-slate-800 rounded-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold flex items-center gap-3">
            Targeted Stack Scan Report
          </h1>
          <p className="text-slate-200 text-sm mt-2 font-mono break-all">
            Session ID: {scanId}
          </p>
        </div>
        
        <ExportCsvButton scanId={scanId} isProcessing={isProcessing} totalFound={stats?.Total} />
      </header>

      <ScanStatsBoard stats={stats} />

      {showLoadingScreen ? (
         <div className="flex flex-col items-center justify-center min-h-[40vh] gap-6 bg-[#262632] rounded-xl p-8">
           <div className="relative">
             <Loader2 className="w-12 h-12 animate-spin text-purple-600" />
           </div>
           
           <div className="text-center space-y-2 text-slate-200">
             <h3 className="text-lg font-bold">
               Analyzing your stack against the OSV database
             </h3>
             <p className="text-sm max-w-md mx-auto leading-relaxed">
               The background workers are securely processing your dependencies. The final report will populate when all packages are complete.
             </p>
           </div>

           <div className="flex flex-col items-center gap-3 w-full max-w-sm">
             <div className="w-full bg-slate-100 rounded-full h-2.5">
               <div 
                 className="bg-purple-600 h-2.5 rounded-full transition-all duration-500" 
                 style={{ width: `${(stats?.processed_packages / stats?.total_packages) * 100 || 0}%` }}
               ></div>
             </div>
             <span className="text-sm font-semibold text-slate-200">
               {stats?.processed_packages || 0} of {stats?.total_packages || 0} Packages Evaluated
             </span>
           </div>

           <div className="flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-full font-mono text-sm font-semibold border border-slate-200">
             <Clock className="w-4 h-4 text-slate-500" />
             Elapsed Time: {formatTime(elapsedTime)}
           </div>
         </div>
      ) : (
        <>
          <div className="grid gap-4">
            {vulnerabilities.map((vuln) => (
              <VulnerabilityCard key={vuln.cve_id} vuln={vuln} />
            ))}
          </div>

          {vulnerabilities.length === 0 && (
            <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl bg-white flex flex-col items-center gap-3">
              <CheckCircle className="w-12 h-12 text-emerald-500" />
              <h3 className="text-lg font-bold">Clean Stack!</h3>
              <p className="text-slate-500 font-medium">No known vulnerabilities were found in your dependencies.</p>
            </div>
          )}

          {vulnerabilities.length > 0 && (
            <div className="mt-8 flex justify-center pb-8">
              {hasNextPage ? (
                <button
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="flex items-center gap-2 px-6 py-2.5 bg-white border border-gray-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors"
                >
                  {isFetchingNextPage ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Loading...</>
                  ) : (
                    <><ChevronDown className="w-4 h-4" /> Load More Results</>
                  )}
                </button>
              ) : (
                <p className="text-slate-400 text-sm font-medium flex items-center gap-2 before:content-[''] before:flex-1 before:h-px before:bg-slate-200 after:content-[''] after:flex-1 after:h-px after:bg-slate-200 w-full max-w-md mx-auto">
                  End of report
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ScanReport;