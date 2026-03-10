import { useState } from 'react';
import { Upload, File, CheckCircle, XCircle, Info, CheckSquare, Square } from 'lucide-react';

const UploadStatements = ({ onUploadSuccess }) => {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [uploadComplete, setUploadComplete] = useState(false);

    // Preview states
    const [previewTransactions, setPreviewTransactions] = useState([]);
    const [selectedIndices, setSelectedIndices] = useState(new Set());
    const [saving, setSaving] = useState(false);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFiles([...files, ...Array.from(e.dataTransfer.files)]);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            setFiles([...files, ...Array.from(e.target.files)]);
        }
    };

    const onUpload = async () => {
        setUploading(true);
        let allParsed = [];
        try {
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('http://127.0.0.1:8000/upload/', {
                    method: 'POST',
                    body: formData,
                });
                if (response.ok) {
                    const result = await response.json();
                    if (result.data) {
                        allParsed = [...allParsed, ...result.data];
                    }
                } else {
                    console.error("Upload failed for", file.name);
                }
            }
            setPreviewTransactions(allParsed);
            setSelectedIndices(new Set(allParsed.map((_, i) => i)));
            setUploadComplete(true);
            setFiles([]);
        } catch (error) {
            console.error("Upload error:", error);
        } finally {
            setUploading(false);
        }
    };

    const onConfirmSave = async () => {
        setSaving(true);
        const toSave = previewTransactions.filter((_, i) => selectedIndices.has(i));
        try {
            const res = await fetch('http://127.0.0.1:8000/transactions/bulk/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toSave)
            });
            if (res.ok) {
                if (onUploadSuccess) onUploadSuccess();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setSaving(false);
        }
    };

    if (previewTransactions.length > 0) {
        return (
            <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <div className="card" style={{ padding: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Validate Extracted Transactions</h3>
                    <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                        We extracted {previewTransactions.length} transactions. Please uncheck any invalid or incorrectly parsed lines before confirming.
                    </p>

                    <div className="table-container" style={{ maxHeight: '500px', overflowY: 'auto', marginBottom: '2rem' }}>
                        <table>
                            <thead style={{ position: 'sticky', top: 0, background: 'var(--surface-color)', zIndex: 10 }}>
                                <tr>
                                    <th style={{ width: '40px', textAlign: 'center' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedIndices.size === previewTransactions.length}
                                            onChange={(e) => {
                                                if (e.target.checked) setSelectedIndices(new Set(previewTransactions.map((_, i) => i)));
                                                else setSelectedIndices(new Set());
                                            }}
                                            style={{ cursor: 'pointer' }}
                                        />
                                    </th>
                                    <th>Date</th>
                                    <th>Description</th>
                                    <th>Account</th>
                                    <th>Bank</th>
                                    <th>Category</th>
                                    <th style={{ textAlign: 'right' }}>Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                {previewTransactions.map((t, i) => {
                                    const isSelected = selectedIndices.has(i);
                                    return (
                                        <tr key={i} className={!isSelected ? "text-muted" : ""} style={{ opacity: !isSelected ? 0.6 : 1, transition: 'all 0.2s', cursor: 'pointer' }} onClick={() => {
                                            const newSet = new Set(selectedIndices);
                                            if (newSet.has(i)) newSet.delete(i);
                                            else newSet.add(i);
                                            setSelectedIndices(newSet);
                                        }}>
                                            <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={() => {
                                                        const newSet = new Set(selectedIndices);
                                                        if (newSet.has(i)) newSet.delete(i);
                                                        else newSet.add(i);
                                                        setSelectedIndices(newSet);
                                                    }}
                                                    style={{ cursor: 'pointer' }}
                                                />
                                            </td>
                                            <td>{t.date}</td>
                                            <td style={{ fontWeight: '600' }}>{t.description}</td>
                                            <td style={{ fontSize: '0.85rem' }}>{t.account_type}</td>
                                            <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{t.bank_name}</td>
                                            <td style={{ fontSize: '0.85rem' }}>
                                                <span style={{ padding: '0.2rem 0.5rem', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--secondary)', borderRadius: '12px' }}>
                                                    {t.category_name}
                                                </span>
                                            </td>
                                            <td style={{ textAlign: 'right', fontWeight: '700', color: isSelected ? (t.amount < 0 ? 'var(--text-primary)' : 'var(--secondary)') : 'inherit' }}>
                                                {t.amount < 0 ? `- $${Math.abs(t.amount).toFixed(2)}` : `+ $${parseFloat(t.amount).toFixed(2)}`}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                        <button className="btn btn-secondary" onClick={() => { setPreviewTransactions([]); setUploadComplete(false); }} disabled={saving}>
                            Cancel
                        </button>
                        <button className="btn btn-primary" onClick={onConfirmSave} disabled={saving || selectedIndices.size === 0}>
                            {saving ? 'Saving...' : `Confirm & Save ${selectedIndices.size} Transactions`}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Upload Bank Statements</h3>

                <div
                    style={{
                        border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
                        borderRadius: 'var(--border-radius-lg)',
                        padding: '3rem',
                        background: dragActive ? 'rgba(79, 70, 229, 0.05)' : 'var(--surface-color-subtle)',
                        transition: 'all 0.3s ease',
                        position: 'relative'
                    }}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <Upload size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
                    <p style={{ fontWeight: '500' }}>Drag and drop your PDF statements here</p>
                    <p className="text-muted">Supports CIBC, BMO, RBC, TD, and Scotiabank</p>

                    <input
                        type="file"
                        multiple
                        accept=".pdf"
                        onChange={handleChange}
                        style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
                    />
                </div>

                {files.length > 0 && (
                    <div style={{ marginTop: '2rem', textAlign: 'left' }}>
                        <h4 style={{ marginBottom: '1rem' }}>Selected Files ({files.length})</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {files.map((file, i) => (
                                <div key={i} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <File size={18} className="text-muted" />
                                        <span>{file.name}</span>
                                    </div>
                                    <XCircle
                                        size={18}
                                        className="text-muted"
                                        style={{ cursor: 'pointer' }}
                                        onClick={() => setFiles(files.filter((_, idx) => idx !== i))}
                                    />
                                </div>
                            ))}
                        </div>

                        <button
                            className="btn btn-primary"
                            style={{ marginTop: '1.5rem', width: '100%' }}
                            onClick={onUpload}
                            disabled={uploading}
                        >
                            {uploading ? 'Processing Statements...' : 'Process Statements'}
                        </button>
                    </div>
                )}

                {uploadComplete && (
                    <div className="animate-fade-in" style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 'var(--border-radius-md)', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--secondary)' }}>
                        <CheckCircle size={20} />
                        <span style={{ fontWeight: '600' }}>Upload successful! Transactions have been extracted.</span>
                    </div>
                )}

                <div style={{ marginTop: '2rem', padding: '1rem', background: 'var(--surface-color-subtle)', borderRadius: 'var(--border-radius-md)', display: 'flex', gap: '0.75rem', textAlign: 'left' }}>
                    <Info size={20} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                    <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: 0 }}>
                        Our system automatically detects the bank format. To prevent duplicate entries, ensure you haven't uploaded the same period statement previously.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default UploadStatements;
