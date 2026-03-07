import { useState, useEffect } from 'react';
import { PieChart, TrendingUp, AlertCircle, DollarSign } from 'lucide-react';

const Dashboard = () => {
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

    const totalExpenses = transactions
        .filter(t => !t.is_internal_transfer && t.amount < 0)
        .reduce((acc, curr) => acc + Math.abs(curr.amount), 0);

    const internalTransfers = transactions
        .filter(t => t.is_internal_transfer)
        .reduce((acc, curr) => acc + Math.abs(curr.amount), 0) / 2;

    const uncategorizedCount = transactions
        .filter(t => !t.category_id && !t.is_internal_transfer)
        .length;

    // Calculate dynamic Top Categories
    const categoryTotals = {};
    transactions.forEach(t => {
        if (!t.is_internal_transfer && t.amount < 0 && t.category) {
            categoryTotals[t.category.name] = (categoryTotals[t.category.name] || 0) + Math.abs(t.amount);
        }
    });

    const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    const topCategories = Object.entries(categoryTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([name, amount], index) => ({
            name,
            amount: amount.toFixed(2),
            color: colors[index % colors.length]
        }));

    const maxCategoryAmount = topCategories.length > 0 ? Math.max(...topCategories.map(c => parseFloat(c.amount))) : 1;

    // Quick mock for Expense Trends based on transaction count (simplified visualization)
    // Real implementation would group by day of week
    const defaultTrends = [10, 20, 15, 30, 25, 40, 20];

    if (loading) return <div className="text-muted">Loading dashboard data...</div>;

    return (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'rgba(79, 70, 229, 0.1)', padding: '0.75rem', borderRadius: '12px', color: 'var(--primary)' }}>
                        <DollarSign size={24} />
                    </div>
                    <div>
                        <div className="text-muted">Total Expenses</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>${totalExpenses.toFixed(2)}</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.75rem', borderRadius: '12px', color: 'var(--secondary)' }}>
                        <TrendingUp size={24} />
                    </div>
                    <div>
                        <div className="text-muted">Savings/Internal</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>${internalTransfers.toFixed(2)}</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '0.75rem', borderRadius: '12px', color: 'var(--danger)' }}>
                        <AlertCircle size={24} />
                    </div>
                    <div>
                        <div className="text-muted">Uncategorized</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>{uncategorizedCount} Items</div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
                <div className="card">
                    <h3>Expense Trends</h3>
                    <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', gap: '1rem', padding: '1rem 0' }}>
                        {defaultTrends.map((h, i) => (
                            <div key={i} style={{ flex: 1, background: 'var(--primary)', height: `${h}%`, borderRadius: '4px 4px 0 0', opacity: 0.7 }}></div>
                        ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }} className="text-muted">
                        <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                    </div>
                </div>

                <div className="card">
                    <h3>Top Categories</h3>
                    {topCategories.length === 0 ? (
                        <p className="text-muted" style={{ marginTop: '1rem' }}>No categorized expenses yet.</p>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                            {topCategories.map(cat => (
                                <div key={cat.name}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                        <span>{cat.name}</span>
                                        <span style={{ fontWeight: '600' }}>${cat.amount}</span>
                                    </div>
                                    <div style={{ width: '100%', height: '6px', background: 'var(--surface-color-subtle)', borderRadius: '3px' }}>
                                        <div style={{ width: `${(parseFloat(cat.amount) / maxCategoryAmount) * 100}%`, height: '100%', background: cat.color, borderRadius: '3px' }}></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
