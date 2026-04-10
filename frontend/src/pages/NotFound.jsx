import { Link } from 'react-router-dom';
import { Home, AlertTriangle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-netbg flex items-center justify-center px-4">
      <div className="text-center">
        <div className="inline-flex p-4 bg-netred/10 rounded-full mb-6">
          <AlertTriangle className="w-12 h-12 text-netred" />
        </div>
        <h1 className="font-sans text-6xl font-bold text-white mb-4">404</h1>
        <p className="text-xl text-gray-400 mb-2">Page Not Found</p>
        <p className="text-sm text-gray-500 mb-8 max-w-md">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/live"
          className="inline-flex items-center gap-2 px-6 py-3 bg-netcyan text-netbg font-semibold rounded-lg hover:bg-netcyan-light transition-all"
        >
          <Home className="w-5 h-5" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
