import { useState, useEffect } from 'react';
import { Calendar, Download, Printer, Filter, User, RotateCcw } from 'lucide-react';

const TaxReport = () => {
    const [provider, setProvider] = useState('');
    const [startDate, setStartDate] = useState('2026-01-01');
    const [endDate, setEndDate] = useState('2026-03-31');

    const [transactions, setTransactions] = useState([]);

    useEffect(() => {
        fetch('http://127.0.0.1:8000/transactions/')
            .then(res => res.json())
            .then(data => setTransactions(data))
            .catch(err => console.error("Error fetching tax report transactions:", err));
    }, []);

    const reportData = transactions.filter(t => {
        const matchesProvider = provider ?
            t.description.toLowerCase().includes(provider.toLowerCase()) ||
            (t.merchandiser && t.merchandiser.toLowerCase().includes(provider.toLowerCase())) : true;
        const matchesStart = startDate ? t.date >= startDate : true;
        const matchesEnd = endDate ? t.date <= endDate : true;

        return matchesProvider && matchesStart && matchesEnd && t.amount < 0 && !t.is_internal_transfer;
    });

    const total = reportData.reduce((acc, curr) => acc + Math.abs(curr.amount), 0);

    return (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="card" style={{ padding: '1.5rem' }}>
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Filter size={20} className="text-muted" />
                    Report Parameters
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                    <div>
                        <label className="text-muted" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem', fontWeight: '600' }}>MERCHANDISER / PROVIDER</label>
                        <div style={{ position: 'relative' }}>
                            <User size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                placeholder="e.g. Shell, Safeway..."
                                style={{ width: '100%', padding: '0.6rem 1rem 0.6rem 2.5rem', borderRadius: 'var(--border-radius-sm)', border: '1px solid var(--border-color)', outline: 'none' }}
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="text-muted" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem', fontWeight: '600' }}>START DATE</label>
                        <input
                            type="date"
                            style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: 'var(--border-radius-sm)', border: '1px solid var(--border-color)', outline: 'none' }}
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-muted" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem', fontWeight: '600' }}>END DATE</label>
                        <input
                            type="date"
                            style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: 'var(--border-radius-sm)', border: '1px solid var(--border-color)', outline: 'none' }}
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-primary" style={{ flex: 1 }}>Generate Report</button>
                    <button className="btn btn-secondary" style={{ flex: 1 }}>
                        <RotateCcw size={16} />
                        Reset
                    </button>
                </div>
            </div>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h3>Report Results</h3>
                        <p className="text-muted" style={{ margin: 0 }}>Showing transactions for "{provider || 'All'}" from {startDate} to {endDate}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button className="btn btn-secondary" style={{ padding: '0.5rem' }} title="Print PDF"><Printer size={18} /></button>
                        <button className="btn btn-secondary" style={{ padding: '0.5rem' }} title="Download CSV"><Download size={18} /></button>
                    </div>
                </div>

                <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Merchandiser</th>
                                <th>Description</th>
                                <th style={{ textAlign: 'right' }}>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reportData.map((row, i) => (
                                <tr key={i}>
                                    <td>{row.date}</td>
                                    <td style={{ fontWeight: '600' }}>{row.description}</td>
                                    <td><span className="text-muted" style={{ fontSize: '0.8rem' }}>{row.account_type || 'Unknown'}</span></td>
                                    <td style={{ textAlign: 'right', fontWeight: '700' }}>$ {Math.abs(row.amount).toFixed(2)}</td>
                                </tr>
                            ))}
                            <tr style={{ background: 'var(--surface-color-subtle)' }}>
                                <td colSpan="3" style={{ textAlign: 'right', fontWeight: '700', textTransform: 'uppercase', fontSize: '0.75rem' }}>Total for Period:</td>
                                <td style={{ textAlign: 'right', fontWeight: '800', fontSize: '1.1rem', color: 'var(--primary)' }}>$ {total.toFixed(2)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TaxReport;
