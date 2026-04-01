import { Activity, ShieldAlert, AlertTriangle, ShieldCheck } from 'lucide-react';

const ScanStatsBoard = ({ stats }) => {
  if (!stats || stats?.total_vulnerabilities === 0) return null;

  const counts = (stats.breakdown || []).reduce((acc, item) => {
    acc[item.label] = item.count;
    return acc;
  }, {});

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div className="bg-[#262632] p-4 rounded-xl flex flex-col items-center text-center">
        <Activity className="w-6 h-6 text-purple-600 mb-2" />
        <span className="text-2xl text-slate-200">{stats?.total_vulnerabilities}</span>
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Total Found</span>
      </div>
      
      <div className="bg-red-50 p-4 rounded-xl flex flex-col items-center text-center">
        <ShieldAlert className="w-6 h-6 text-red-600 mb-2" />
        <span className="text-2xl font-black text-red-800">{counts['Very Promising'] || 0}</span>
        <span className="text-xs font-bold text-red-600 uppercase tracking-wide">Critical Exploits</span>
      </div>
      
      <div className="bg-amber-50 p-4 rounded-xl flex flex-col items-center text-center">
        <AlertTriangle className="w-6 h-6 text-amber-600 mb-2" />
        <span className="text-2xl font-black text-amber-800">{counts['Slightly Promising'] || 0}</span>
        <span className="text-xs font-bold text-amber-600 uppercase tracking-wide">Moderate Risks</span>
      </div>
      
      <div className="bg-emerald-50 p-4 rounded-xl flex flex-col items-center text-center">
        <ShieldCheck className="w-6 h-6 text-emerald-600 mb-2" />
        <span className="text-2xl font-black text-emerald-800">{counts['Not Promising'] || 0}</span>
        <span className="text-xs font-bold text-emerald-600 uppercase tracking-wide">Low Priority</span>
      </div>
    </div>
  );
};

export default ScanStatsBoard;