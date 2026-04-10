'use client';

/**
 * ReportButton — OR-14, OR-15
 *
 * Reusable component to flag abusive, fraudulent, or non-compliant users/providers.
 * Opens a modal with a category dropdown and description field.
 */

import { useState } from 'react';
import { Flag, X, AlertTriangle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface ReportButtonProps {
  reportedId: string;
  reportedName: string;
  buttonClass?: string;
  buttonText?: string;
}

const CATEGORIES = [
  { value: 'fraud', label: 'Fraud or Fake Listing' },
  { value: 'abuse', label: 'Abuse or Harassment' },
  { value: 'non_compliance', label: 'Violating Terms' },
  { value: 'quality', label: 'Severe Quality Misrepresentation' },
  { value: 'safety', label: 'Health or Safety Concern' },
  { value: 'other', label: 'Other Issue' },
];

export default function ReportButton({ reportedId, reportedName, buttonClass, buttonText }: ReportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [category, setCategory] = useState('fraud');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) {
      setError('Please provide a brief description.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      const resp = await fetch('/api/v1/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          reported_id: reportedId,
          category,
          description
        })
      });

      if (!resp.ok) throw new Error((await resp.json()).error || 'Failed to submit report');
      
      setSuccess(true);
      setTimeout(() => {
        setIsOpen(false);
        setSuccess(false);
        setDescription('');
      }, 2500);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className={clsx(
          "flex items-center gap-1.5 text-xs text-rose-400 hover:bg-rose-900/20 px-2 py-1 rounded transition-colors",
          buttonClass
        )}
      >
        <Flag className="w-3.5 h-3.5" />
        {buttonText || 'Report'}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden mt-10">
            
            <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
              <h3 className="font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                Report {reportedName}
              </h3>
              <button 
                onClick={() => !loading && setIsOpen(false)}
                className="text-zinc-500 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {success ? (
              <div className="p-8 text-center bg-zinc-900">
                <div className="w-12 h-12 bg-emerald-900/40 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Flag className="w-6 h-6 text-emerald-400" />
                </div>
                <h4 className="text-white font-bold text-lg">Report Submitted</h4>
                <p className="text-zinc-400 text-sm mt-2">
                  Thank you for keeping CultivaX safe. Our admin team will review this shortly.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="p-5 space-y-4">
                <p className="text-xs text-zinc-400 bg-zinc-800/50 p-3 rounded-lg border border-zinc-800">
                  Use this form to flag suspicious or abusive behavior. False reporting may result in account suspension.
                </p>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">Reason for reporting</label>
                  <select 
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-600"
                  >
                    {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">Details</label>
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
                    placeholder="Please provide specific details..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-rose-600"
                  />
                </div>

                {error && <p className="text-xs text-rose-400 font-semibold">{error}</p>}

                <div className="flex gap-3 pt-2">
                  <button 
                    type="button"
                    onClick={() => setIsOpen(false)} 
                    className="flex-1 py-2 rounded-xl bg-zinc-800 text-white font-semibold hover:bg-zinc-700 transition"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-2 rounded-xl bg-rose-600 text-white font-semibold hover:bg-rose-500 transition disabled:opacity-50 flex justify-center items-center gap-2"
                  >
                    {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                    Submit Report
                  </button>
                </div>
              </form>
            )}

          </div>
        </div>
      )}
    </>
  );
}
