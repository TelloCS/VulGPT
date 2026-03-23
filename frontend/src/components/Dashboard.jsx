import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useVulnerabilities } from '../hooks/useVulnerabilities';
import { useUploadManifest } from '../hooks/useUploadManifest';
import VulnerabilityCard from './VulnerabilityCard';
import { Loader2, ChevronDown, Search, Filter, UploadCloud } from 'lucide-react';
import { useDebounce } from 'use-debounce';

const Dashboard = () => {
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState('');
  const [classificationFilter, setClassificationFilter] = useState('All');
  const [debouncedSearch] = useDebounce(searchInput, 500);

  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  } = useVulnerabilities(debouncedSearch || searchInput, classificationFilter);

  // File Upload Setup
  const fileInputRef = useRef(null);
  const uploadMutation = useUploadManifest();

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const loadingToastId = toast.loading(`Uploading ${file.name}...`);

      uploadMutation.mutate(file, {
        onSuccess: (responseData) => {
          toast.success('Scan queued successfully! Redirecting...', { id: loadingToastId });
          navigate(`/scan/${responseData.scan_id}`);
        },
        onError: (err) => {
          toast.error(err.response?.data?.error || "Failed to process the manifest file.", { id: loadingToastId });
        }
      });
      event.target.value = '';
    }
  };

  if (isError) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg max-w-5xl mx-auto m-4">
        <h2 className="text-red-800 text-sm font-bold">Connection Error</h2>
        <p className="text-red-600 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  const vulnerabilities = data?.pages.flatMap(page => page.items) || [];

  return (
    <div className="px-4 md:px-6 max-w-6xl mx-auto">

      {/* Search & Action Bar */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#262632] p-4 rounded-xl">

        <div className="w-full md:w-auto">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".json,.txt,.in"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
            className="w-full md:w-auto flex items-center justify-center gap-2 px-5 py-2.5 bg-purple-600 text-white
            text-sm font-semibold hover:bg-purple-700 disabled:opacity-50 transition-colors whitespace-nowrap rounded-md"
          >
            {uploadMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <UploadCloud className="w-5 h-5" />
            )}
            {uploadMutation.isPending ? 'Uploading & Scanning...' : 'Scan Stack File'}
          </button>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto text-slate-200">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
            <input
              type="text"
              placeholder="Search CVE or keyword..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-[#30313e] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>

          <div className="relative w-full sm:w-60">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" />
            <select
              value={classificationFilter}
              onChange={(e) => setClassificationFilter(e.target.value)}
              className="w-full pl-10 pr-8 py-2 bg-[#30313e] rounded-lg text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-purple-400"
            >
              <option value="All">All Severity Levels</option>
              <option value="Very Promising">Very Promising</option>
              <option value="Slightly Promising">Slightly Promising</option>
              <option value="Not Promising">Not Promising</option>
            </select>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          <p className="text-slate-500 text-sm font-medium">Querying Graph Database...</p>
        </div>
      ) : (
        <>
          <div className="grid gap-4">
            {vulnerabilities.length > 0 ? (
              vulnerabilities.map((vuln) => (
                <VulnerabilityCard key={vuln.cve_id} vuln={vuln} />
              ))
            ) : (
              <div className="text-center py-16 rounded-xl bg-[#262632]">
                <p className="text-slate-200 font-medium">No vulnerabilities match your search criteria.</p>
              </div>
            )}
          </div>

          {vulnerabilities.length > 0 && (
            <div className="mt-8 flex justify-center pb-8">
              {hasNextPage ? (
                <button
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="flex items-center gap-2 px-6 py-2.5 bg-[#262632] text-slate-200 text-sm font-semibold rounded-lg"
                >
                  {isFetchingNextPage ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Loading More...</>
                  ) : (
                    <><ChevronDown className="w-4 h-4" /> Load More Results</>
                  )}
                </button>
              ) : (
                <p className="text-slate-200 text-sm font-medium flex items-center gap-2 before:content-[''] before:flex-1 before:h-px before:bg-slate-200 after:content-[''] after:flex-1 after:h-px after:bg-slate-200 w-full max-w-md mx-auto">
                  End of database
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;