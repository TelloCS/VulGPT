import { Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      <Toaster 
        position="bottom-right"
        toastOptions={{
          className: 'text-sm font-medium text-slate-800',
          success: {
            iconTheme: { primary: '#10b981', secondary: '#fff' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#fff' },
          },
        }} 
      />
      <Navbar />
      <main className="w-full flex-grow p-8 font-mono bg-[#30313e]">
        <Outlet />
      </main>
    </div>
  );
}

export default App;