'use client';

import { useSession } from 'next-auth/react';
import { signIn, signOut } from '@/lib/auth-client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';

export default function Home() {
  const { data: session, status } = useSession();
  const [isVerifying, setIsVerifying] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [hasAttemptedVerification, setHasAttemptedVerification] = useState(false);
  const router = useRouter();

  const verifyDiscordAdmin = useCallback(async () => {
    if (!session || hasAttemptedVerification) return;
    
    setIsVerifying(true);
    setHasAttemptedVerification(true);
    
    try {
      console.log('Starting Discord admin verification...');
      
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          discord_user_id: session.user.discordId 
        }),
      });

      const data = await response.json();
      console.log('Verification response:', data);
      
      if (response.ok && data.success) {
        setIsAuthorized(true);
        toast.success('Welcome to Godfather by AIS!');
        router.push('/dashboard');
      } else {
        throw new Error(data.error || 'Verification failed');
      }
    } catch (error: unknown) {
      console.error('Verification error:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Access denied. Godfather role required.';
      toast.error(errorMessage);
      
      setIsAuthorized(false);
    }
    setIsVerifying(false);
  }, [session, hasAttemptedVerification, router]);

  useEffect(() => {
    // Only verify if user is signed in and we haven't attempted yet
    if (status !== 'loading' && session && !isAuthorized && !hasAttemptedVerification) {
      verifyDiscordAdmin();
    }
  }, [status, session, isAuthorized, hasAttemptedVerification, verifyDiscordAdmin]);

  const handleSignIn = async () => {
    await signIn('discord', { callbackUrl: '/dashboard' });
  };

  const handleSignOut = async () => {
    await signOut({ callbackUrl: '/' });
    setHasAttemptedVerification(false);
    setIsAuthorized(false);
  };

  // Show loading state only while session is loading
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
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

  if (session && isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
          </div>
          <p className="text-gray-300">Verifying access...</p>
        </div>
      </div>
    );
  }

  if (session && hasAttemptedVerification && !isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
        <div className="max-w-md w-full bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 shadow-2xl p-8 text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
            <p className="text-gray-400">
              You need the Godfather role in the AI Society Discord server to access this platform.
            </p>
            <p className="text-gray-500 text-sm mt-3">
              Please contact a server administrator if you believe this is an error.
            </p>
          </div>
          <div className="flex justify-center">
            <button
              onClick={handleSignOut}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
        <Toaster />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <div className="inline-block mb-6">
              <div className="flex items-center justify-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                </div>
                <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
                  Godfather
                </h1>
              </div>
            </div>
            
            <p className="text-xl text-gray-300 mb-4">
              AI Society ASU Development Platform
            </p>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Access powerful GPU computing resources for your AI and machine learning projects. 
              Connect seamlessly to managed RunPod environments with your team.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-purple-500/50 transition-all">
              <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">GPU Computing</h3>
              <p className="text-gray-400 text-sm">Access NVIDIA GPUs for training and inference</p>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-pink-500/50 transition-all">
              <div className="w-12 h-12 bg-pink-500/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">Secure Access</h3>
              <p className="text-gray-400 text-sm">Discord-based authentication for team members</p>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-blue-500/50 transition-all">
              <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">CLI Tool</h3>
              <p className="text-gray-400 text-sm">Connect via terminal for seamless development</p>
            </div>
          </div>

          {/* Sign In Card */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 shadow-2xl">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                Get Started
              </h2>
              <p className="text-gray-400">
                Sign in with your Discord account to access the platform
              </p>
            </div>

            <div className="flex justify-center mb-6">
              {!session ? (
                <button
                  onClick={handleSignIn}
                  className="w-full max-w-md bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 px-8 rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 transition-all duration-200 flex items-center justify-center space-x-3 shadow-lg hover:shadow-purple-500/50"
                >
                  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
                  </svg>
                  <span>Sign in with Discord</span>
                </button>
              ) : (
                <button
                  onClick={handleSignOut}
                  className="bg-gray-700 text-white px-6 py-3 rounded-xl hover:bg-gray-600 transition-colors"
                >
                  Sign Out
                </button>
              )}
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-500">
                For AI Society ASU Discord members
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-8 text-gray-500 text-sm">
            <p>Made with ❤️ by AI Society at Arizona State University</p>
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
}