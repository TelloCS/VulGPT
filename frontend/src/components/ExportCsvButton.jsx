import { Download } from 'lucide-react';

const ExportCsvButton = ({ scanId, isProcessing, totalFound }) => {
  if (isProcessing || !totalFound || totalFound === 0) {
    return null; 
  }

  return (
    <a 
      href={`/api/scans/${scanId}/export/`} 
      download={`vulgpt_scan_${scanId}.csv`}
      className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-purple-600 text-white text-sm font-semibold rounded-lg hover:bg-purple-700 transition-colors whitespace-nowrap"
    >
      <Download className="w-5 h-5" /> 
      Export to CSV
    </a>
  );
};

export default ExportCsvButton;