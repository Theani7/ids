import PCAPUpload from '../components/PCAPUpload';
import { FileCode } from 'lucide-react';

export default function PCAPAnalyzer() {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 flex items-center justify-between border-b border-netborder bg-netsurface/50">
        <h2 className="font-orbitron text-xl text-netcyan tracking-wide flex items-center gap-2">
          <FileCode className="w-6 h-6" />
          PCAP File Analysis
        </h2>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          <PCAPUpload />
        </div>
      </div>
    </div>
  );
}
