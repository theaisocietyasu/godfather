'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import toast, { Toaster } from 'react-hot-toast';
import { Copy as CopyIcon, Check as CheckIcon, Terminal as TerminalIcon } from 'lucide-react';
import Navbar from '@/components/Navbar';

export default function CLIAuth() {
  const { data: session, status } = useSession();
  const [token, setToken] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (status === 'loading') return;
    
    if (!session) {
      router.push('/');
      return;
    }

    const fetchToken = async () => {
      try {
        // Verify user role with backend
        const response = await fetch('/api/auth/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ discord_user_id: session.user.discordId })
        });

        if (response.ok) {
          const data = await response.json();
          setIsAdmin(data.is_admin || false);
        }

        // Generate CLI token
        const customToken = `discord_${session.user.discordId}_${Date.now()}`;
        setToken(customToken);
      } catch (error) {
        console.error('Error generating token:', error);
        toast.error('Failed to generate authentication token');
      } finally {
        setLoading(false);
      }
    };

    fetchToken();
  }, [session, status, router]);

  const copyToken = async () => {
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
      toast.success('Token copied to clipboard!');
      setTimeout(() => setCopied(false), 3000);
    } catch (error) {
      console.error('Error copying token:', error);
      toast.error('Failed to copy token');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
          </div>
          <p className="text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* <Navbar /> */}

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-gray-800 shadow-lg rounded-lg p-8 border border-gray-700">
          <div className="flex items-center space-x-3 mb-6">
            <TerminalIcon className="w-8 h-8 text-purple-500" />
            <h2 className="text-2xl font-bold text-white">CLI Authentication Token</h2>
          </div>

          <div className="space-y-6">
            {/* Instructions */}
            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
              <h3 className="font-semibold text-blue-300 mb-2">How to use:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-blue-200">
                <li>Copy the token below by clicking the copy button</li>
                <li>Run the Godfather CLI tool: <code className="bg-blue-800 px-2 py-1 rounded text-blue-100">godfather</code></li>
                <li>When prompted for authentication, paste the token</li>
                <li>
                  {isAdmin 
                    ? "You'll have full admin access to manage all pods"
                    : "You'll have access to view and connect to available pods"}
                </li>
              </ol>
            </div>

            {/* Role Badge */}
            {isAdmin ? (
              <div className="bg-cyan-900/30 border border-cyan-700 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">👑</span>
                  <div>
                    <h3 className="font-semibold text-cyan-300">Admin Access</h3>
                    <p className="text-sm text-cyan-200">You have full administrative privileges</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">👤</span>
                  <div>
                    <h3 className="font-semibold text-green-300">Member Access</h3>
                    <p className="text-sm text-green-200">You can view and connect to available pods</p>
                  </div>
                </div>
              </div>
            )}

            {/* Token Display */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Your Authentication Token
              </label>
              <div className="relative">
                <textarea
                  readOnly
                  value={token}
                  className="w-full px-4 py-3 pr-12 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 font-mono text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={6}
                  onClick={(e) => e.currentTarget.select()}
                />
                <button
                  onClick={copyToken}
                  className="absolute right-2 top-2 p-2 bg-gray-600 border border-gray-500 rounded-md hover:bg-gray-500 transition-colors"
                  title="Copy token"
                >
                  {copied ? (
                    <CheckIcon className="w-5 h-5 text-green-400" />
                  ) : (
                    <CopyIcon className="w-5 h-5 text-gray-300" />
                  )}
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-400">
                This token expires after a period of time. If you get authentication errors, come back here to get a fresh token.
              </p>
            </div>

            {/* Quick Copy Button */}
            <button
              onClick={copyToken}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all flex items-center justify-center space-x-2"
            >
              {copied ? (
                <>
                  <CheckIcon className="w-5 h-5" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <CopyIcon className="w-5 h-5" />
                  <span>Copy Token</span>
                </>
              )}
            </button>

            {/* CLI Example */}
            <div className="bg-gray-950 border border-gray-700 text-gray-100 rounded-lg p-4 font-mono text-sm">
              <div className="text-gray-500 mb-2"># Example CLI Usage</div>
              <div className="space-y-1">
                <div className="text-green-400">$ godfather</div>
                <div className="text-white">🎯 What would you like to do?</div>
                <div className="text-white">  1. List available pods</div>
                <div className="text-white">  2. Connect to a pod</div>
                <div className="text-white">  3. Show status</div>
                <div className="text-white">  4. Logout</div>
                <div className="text-white">  5. Exit</div>
                <div className="mt-2 text-green-400">Enter your choice (1-5): 1</div>
                <div className="text-white">📡 Fetching available pods...</div>
                <div className="text-yellow-400">🔐 Authentication required...</div>
                <div className="text-white">Enter your authentication token: <span className="text-gray-600">[paste token here]</span></div>
              </div>
            </div>

            {/* Security Warning */}
            <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-300 mb-2">⚠️ Security Notice:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-200">
                <li>Keep this token secure - it provides access to your account</li>
                <li>Don&apos;t share this token with anyone</li>
                <li>Don&apos;t commit this token to version control</li>
                <li>Tokens expire automatically for security</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      <Toaster />
    </div>
  );
}
