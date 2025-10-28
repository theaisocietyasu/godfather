'use client';

import { useAuth, UserButton } from '@clerk/nextjs';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';
import { Copy as CopyIcon, Check as CheckIcon, Terminal as TerminalIcon } from 'lucide-react';

export default function CLIAuth() {
  const { isSignedIn, getToken } = useAuth();
  const [token, setToken] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/');
      return;
    }

    const fetchToken = async () => {
      try {
        const authToken = await getToken();
        if (authToken) {
          setToken(authToken);
        }
      } catch (error) {
        console.error('Error fetching token:', error);
        toast.error('Failed to fetch authentication token');
      } finally {
        setLoading(false);
      }
    };

    fetchToken();
  }, [isSignedIn, getToken, router]);

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">AI Society Admin Portal</h1>
              <span className="text-sm text-gray-500">CLI Authentication</span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg font-medium transition-colors"
              >
                ← Back to Dashboard
              </button>
              <UserButton />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white shadow rounded-lg p-8">
          <div className="flex items-center space-x-3 mb-6">
            <TerminalIcon className="w-8 h-8 text-purple-600" />
            <h2 className="text-2xl font-bold text-gray-900">CLI Authentication Token</h2>
          </div>

          <div className="space-y-6">
            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">How to use:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
                <li>Copy the token below by clicking the copy button</li>
                <li>Run the Godfather CLI tool: <code className="bg-blue-100 px-2 py-1 rounded">godfather</code></li>
                <li>When prompted for authentication, paste the token</li>
                <li>You&apos;ll now have access to public pods via the CLI</li>
              </ol>
            </div>

            {/* Token Display */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Authentication Token
              </label>
              <div className="relative">
                <textarea
                  readOnly
                  value={token}
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={6}
                  onClick={(e) => e.currentTarget.select()}
                />
                <button
                  onClick={copyToken}
                  className="absolute right-2 top-2 p-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  title="Copy token"
                >
                  {copied ? (
                    <CheckIcon className="w-5 h-5 text-green-600" />
                  ) : (
                    <CopyIcon className="w-5 h-5 text-gray-600" />
                  )}
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                This token expires after a period of time. If you get authentication errors, come back here to get a fresh token.
              </p>
            </div>

            {/* Quick Copy Button */}
            <button
              onClick={copyToken}
              className="w-full bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2"
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
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm">
              <div className="text-gray-400 mb-2"># Example CLI Usage</div>
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
                <div className="text-white">Enter your authentication token: <span className="text-gray-500">[paste token here]</span></div>
              </div>
            </div>

            {/* Security Warning */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Security Notice:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
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
