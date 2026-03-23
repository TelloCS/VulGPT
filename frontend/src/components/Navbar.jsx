import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';

const Navbar = () => {
  return (
    <nav className="bg-[#262632] sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-xl font-extrabold text-white tracking-tight">
              VulGPT <span className="text-slate-200 font-medium text-sm ml-1 hidden sm:inline">| Automated Security Analysis</span>
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <a 
              href="https://github.com" 
              target="_blank" 
              rel="noreferrer"
              className="text-slate-200 hover:text-white transition-colors"
              title="View Source Code"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;