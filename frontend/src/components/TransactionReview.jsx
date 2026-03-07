import { useState, useEffect } from 'react';
import { Search, Filter, Edit2, RotateCcw, Check, ArrowRightLeft } from 'lucide-react';

const TransactionReview = () => {
    const [searchTerm, setSearchTerm] = useState('');

    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://127.0.0.1:8000/transactions/')
            .then(res => res.json())
            .then(data => {
                setTransactions(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching transactions:", err);
                setLoading(false);
            });
    }, []);

    return (
        <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', gap: '1rem' }}>
                <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        type="text"
                        placeholder="Search merchants or descriptions..."
                        style={{
                            width: '100%',
                            padding: '0.75rem 1rem 0.75rem 2.75rem',
                            borderRadius: 'var(--border-radius-md)',
                            border: '1px solid var(--border-color)',
                            outline: 'none',
                            fontSize: '0.9rem'
                        }}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <button className="btn btn-secondary">
                    <Filter size={18} />
                    Filter
                </button>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Account</th>
                            <th>Category</th>
                            <th style={{ textAlign: 'right' }}>Amount</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.filter(t => t.description.toLowerCase().includes(searchTerm.toLowerCase())).map(t => (
                            <tr key={t.id} className="hover-row">
                                <td style={{ fontSize: '0.85rem' }}>{t.date}</td>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        {t.is_internal_transfer && <ArrowRightLeft size={14} style={{ color: 'var(--primary)' }} />}
                                        <span style={{ fontWeight: '500' }}>{t.description}</span>
                                    </div>
                                </td>
                                <td>
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <span className="text-muted" style={{ fontSize: '0.8rem' }}>{t.account_type || 'Unknown'}</span>
                                        {t.bank_name && <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>{t.bank_name}</span>}
                                    </div>
                                </td>
                                <td>
                                    <span style={{
                                        padding: '0.25rem 0.6rem',
                                        borderRadius: '20px',
                                        fontSize: '0.75rem',
                                        fontWeight: '600',
                                        background: t.is_internal_transfer ? 'rgba(79, 70, 229, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                                        color: t.is_internal_transfer ? 'var(--primary)' : 'var(--secondary)'
                                    }}>
                                        {t.category ? t.category.name : (t.is_internal_transfer ? 'Transfer' : 'Uncategorized')}
                                    </span>
                                </td>
                                <td style={{ textAlign: 'right', fontWeight: '700', color: t.amount < 0 ? 'var(--text-primary)' : 'var(--secondary)' }}>
                                    {t.amount < 0 ? `- $${Math.abs(t.amount).toFixed(2)}` : `+ $${t.amount.toFixed(2)}`}
                                </td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button className="btn btn-secondary" style={{ padding: '0.4rem' }} title="Edit Category">
                                            <Edit2 size={14} />
                                        </button>
                                        <button className="btn btn-secondary" style={{ padding: '0.4rem' }} title="Flag as Transfer">
                                            <RotateCcw size={14} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TransactionReview;
