'use client';

/**
 * Registration Page
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'farmer',
    region: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const { confirmPassword, ...registrationData } = formData;
      await register(registrationData);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-cultivax-bg py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold">
            <span className="text-cultivax-primary">Cultiva</span>
            <span className="text-cultivax-accent">X</span>
          </h1>
          <p className="text-gray-500 mt-2">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Full Name</label>
            <input name="full_name" value={formData.full_name} onChange={handleChange} placeholder="Enter your full name" required className="w-full" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Phone Number</label>
            <input name="phone" type="tel" value={formData.phone} onChange={handleChange} placeholder="Enter phone number" required className="w-full" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Email (Optional)</label>
            <input name="email" type="email" value={formData.email} onChange={handleChange} placeholder="Enter email" className="w-full" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Region</label>
            <input name="region" value={formData.region} onChange={handleChange} placeholder="e.g. Rajasthan" className="w-full" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Role</label>
            <select name="role" value={formData.role} onChange={handleChange} className="w-full bg-cultivax-surface border border-cultivax-card rounded-lg px-4 py-2.5 text-white">
              <option value="farmer">Farmer</option>
              <option value="provider">Service Provider</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
            <input name="password" type="password" value={formData.password} onChange={handleChange} placeholder="Min 6 characters" required className="w-full" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Confirm Password</label>
            <input name="confirmPassword" type="password" value={formData.confirmPassword} onChange={handleChange} placeholder="Confirm password" required className="w-full" />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating account...' : 'Create Account'}
          </button>

          <p className="text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link href="/login" className="text-cultivax-primary hover:underline">
              Sign In
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
