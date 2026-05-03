import { useState, useRef } from 'react';
import { uploadPCAP } from '../services/api';
import { Upload, File, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export default function PCAPUpload() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFile = async (file) => {
    if (!file.name.endsWith('.pcap') && !file.name.endsWith('.pcapng')) {
      setError('Only .pcap or .pcapng files are supported');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const data = await uploadPCAP(file);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze PCAP file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
        <Upload className="w-4 h-4" />
        PCAP File Analysis
      </h2>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded p-8 text-center cursor-pointer transition-all ${
          dragging
            ? 'border-netcyan bg-netcyan/10'
            : 'border-netborder bg-netsurface hover:border-netgreen hover:bg-netgreen/5'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pcap,.pcapng"
          onChange={handleFileInput}
          className="hidden"
        />
        <File className="w-10 h-10 text-[#5a6a7a] mx-auto mb-3" />
        <p className="text-sm font-mono text-[#e6edf3] mb-1">
          Drop PCAP file here or click to browse
        </p>
        <p className="text-xs font-mono text-[#5a6a7a]">
          Supports .pcap and .pcapng formats
        </p>
      </div>

      {uploading && (
        <div className="text-center py-4">
          <div className="animate-spin w-6 h-6 border-2 border-netcyan border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-xs font-mono text-netcyan animate-pulse">
            Analyzing packets...
          </p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 rounded bg-netred/10 border border-netred/30">
          <XCircle className="w-5 h-5 text-netred" />
          <p className="text-sm font-mono text-netred">{error}</p>
        </div>
      )}

      {result && (
        <div className="border border-netborder bg-netsurface rounded p-4 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-netgreen" />
            <span className="text-sm font-mono text-netgreen">
              Analysis Complete: {result.filename}
            </span>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-netbg rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Flows</p>
              <p className="text-xl font-mono text-netcyan">{result.flows_analyzed?.toLocaleString()}</p>
            </div>
            <div className="bg-netbg rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Malicious</p>
              <p className={`text-xl font-mono ${result.malicious_detected > 0 ? 'text-netred' : 'text-netgreen'}`}>
                {result.malicious_detected}
              </p>
            </div>
            <div className="bg-netbg rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Threat Rate</p>
              <p className="text-xl font-mono text-netorange">
                {result.flows_analyzed > 0
                  ? ((result.malicious_detected / result.flows_analyzed) * 100).toFixed(1)
                  : 0}%
              </p>
            </div>
          </div>

          {/* Protocols */}
          {result.protocols && Object.keys(result.protocols).length > 0 && (
            <div>
              <p className="text-xs font-mono uppercase text-[#8b9ab3] mb-2">Protocol Distribution</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(result.protocols).map(([proto, count]) => (
                  <span
                    key={proto}
                    className="text-xs font-mono px-2 py-1 rounded bg-netbg text-netcyan"
                  >
                    {proto}: {count}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Alerts */}
          {result.alerts && result.alerts.length > 0 && (
            <div>
              <p className="text-xs font-mono uppercase text-[#8b9ab3] mb-2 flex items-center gap-2">
                <AlertCircle className="w-3 h-3" />
                Detected Threats ({result.alerts.length})
              </p>
              <div className="max-h-48 overflow-y-auto space-y-1">
                {result.alerts.slice(0, 20).map((alert, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-2 rounded bg-netred/10 border border-netred/30"
                  >
                    <span className="text-xs font-mono text-netred">●</span>
                    <span className="text-xs font-mono text-[#e6edf3]">
                      {alert.src_ip}:{alert.src_port} → {alert.dst_ip}:{alert.dst_port}
                    </span>
                    <span className="text-xs font-mono text-[#8b9ab3]">{alert.protocol}</span>
                    <span className="text-xs font-mono text-netorange">
                      {(alert.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
                {result.alerts.length > 20 && (
                  <p className="text-xs font-mono text-[#5a6a7a] text-center py-2">
                    +{result.alerts.length - 20} more alerts...
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
