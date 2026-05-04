import { useState, useRef } from 'react';
import { UploadCloud, FileType, CheckCircle, AlertTriangle } from 'lucide-react';
import { batchAnalyze } from '../services/api';
import StatCard from '../components/ui/StatCard';

export default function BatchAnalyzer() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setResults(null);
      setError('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setResults(null);
      setError('');
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const data = await batchAnalyze(file);
      setResults(data.results);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze the file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 flex items-center justify-between border-b border-netborder bg-netsurface/50">
        <h2 className="font-orbitron text-xl text-netcyan tracking-wide">Batch Analyzer</h2>
      </div>

      <div className="p-6 max-w-4xl mx-auto w-full">
        <div className="bg-netsurface border border-netborder rounded-xl p-8 mb-8 text-center shadow-lg">
          <div
            className={`border-2 border-dashed ${file ? 'border-netgreen' : 'border-[#2a3a4e]'} rounded-lg p-12 transition-colors duration-200 ease-in-out cursor-pointer hover:bg-netbg/50`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv"
              className="hidden"
            />
            {file ? (
              <div className="flex flex-col items-center">
                <FileType size={48} className="text-netgreen mb-4" />
                <p className="text-sm text-netgreen font-bold mb-1">{file.name}</p>
                <p className="text-xs text-[#8b9ab3]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <UploadCloud size={48} className="text-[#8b9ab3] mb-4" />
                <p className="text-sm text-[#e6edf3] mb-2 font-bold tracking-wide">Drag & Drop PCAP CSV File Here</p>
                <p className="text-xs text-[#8b9ab3]">or click to browse from your machine</p>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-6 bg-netred/10 border border-netred text-netred px-4 py-3 rounded text-sm text-left flex items-start gap-3">
              <AlertTriangle className="shrink-0" size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="mt-8 flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="px-8 py-3 bg-netcyan text-netbg font-bold uppercase tracking-widest rounded hover:bg-[#00b3d6] transition-colors disabled:opacity-50 min-w-[200px]"
            >
              {loading ? 'Processing ML Pipeline...' : 'Run Analysis'}
            </button>
          </div>
        </div>

        {/* Results Section */}
        {results && (
          <div className="animate-fade-in space-y-6">
            <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
              <CheckCircle size={14} className="text-netgreen" />
              Analysis Complete
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard
                title="Total Extracted Flows"
                value={results.total.toLocaleString()}
                subtitle="From uploaded CSV"
                color="cyan"
              />
              <StatCard
                title="Malicious Flows"
                value={results.malicious.toLocaleString()}
                subtitle="Threats identified"
                color="red"
              />
              <StatCard
                title="Detection Ratio"
                value={results.total > 0 ? `${((results.malicious / results.total) * 100).toFixed(1)}%` : '0%'}
                subtitle="Malicious / Total"
                color="green"
              />
            </div>

            {/* Threat Breakdown */}
            {results.malicious > 0 && results.attack_types && Object.keys(results.attack_types).length > 0 && (
              <div className="bg-netsurface border border-netborder rounded-xl p-6">
                <h4 className="text-xs font-mono uppercase tracking-[0.1em] text-[#8b9ab3] mb-4">
                  Threat Breakdown
                </h4>
                <div className="space-y-4">
                  {Object.entries(results.attack_types)
                    .sort(([, a], [, b]) => b - a)
                    .map(([type, count]) => {
                      const percentage = (count / results.malicious) * 100;
                      return (
                        <div key={type} className="space-y-1.5">
                          <div className="flex justify-between text-xs font-mono">
                            <span className="text-white">{type}</span>
                            <span className="text-netred">{count.toLocaleString()} flows ({percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full h-1.5 bg-netbg rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-netred rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
