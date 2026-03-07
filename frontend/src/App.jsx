import { useState } from 'react';
import { Home, Upload, FileText, PieChart } from 'lucide-react';
import Dashboard from './components/Dashboard';
import UploadStatements from './components/UploadStatements';
import TransactionReview from './components/TransactionReview';
import TaxReport from './components/TaxReport';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return <Dashboard />;
      case 'upload': return <UploadStatements onUploadSuccess={() => setActiveTab('review')} />;
      case 'review': return <TransactionReview />;
      case 'report': return <TaxReport />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <nav className="sidebar">
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Family Expenses</h2>
          <span className="text-muted">Personal Finance Tracker</span>
        </div>

        <button
          className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
          style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
        >
          <Home size={18} />
          <span>Dashboard</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
          style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
        >
          <Upload size={18} />
          <span>Upload PDF</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => setActiveTab('review')}
          style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
        >
          <FileText size={18} />
          <span>Transactions</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'report' ? 'active' : ''}`}
          onClick={() => setActiveTab('report')}
          style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
        >
          <PieChart size={18} />
          <span>Tax Reports</span>
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="glass-card" style={{ minHeight: '80vh' }}>
          <h1 style={{ marginBottom: '2rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
            {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </h1>
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
