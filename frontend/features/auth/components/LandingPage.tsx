'use client';

import { useSession } from 'next-auth/react';
import { signIn, signOut } from '@/lib/auth-client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';
import { Cpu, ShieldCheck, Terminal, TriangleAlert, Zap } from 'lucide-react';
import { verifyDiscordUser } from '@/features/auth/api';
import { LoadingScreen } from '@/components/Skeleton';
import Button from '@/components/Button';

export default function LandingPage() {
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
      const data = await verifyDiscordUser(session.user.discordId);

      if (data.success) {
        setIsAuthorized(true);
        if (data.is_admin) {
          toast.success('Signed in to the Godfather admin portal');
          router.push('/dashboard');
        } else {
          toast.success('Signed in. Redirecting to CLI authentication.');
          router.push('/cli-auth');
        }
      } else {
        throw new Error(data.error || 'Verification failed');
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : 'Access denied. You must be a member of the AI Society Discord.';
      toast.error(errorMessage);
      setIsAuthorized(false);
    }
    setIsVerifying(false);
  }, [session, hasAttemptedVerification, router]);

  useEffect(() => {
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

  if (status === 'loading') {
    return <LoadingScreen />;
  }

  if (session && isVerifying) {
    return <LoadingScreen label="Verifying access" />;
  }

  if (session && hasAttemptedVerification && !isAuthorized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg p-4">
        <div className="glass w-full max-w-md rounded-2xl p-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-danger-soft">
            <TriangleAlert className="h-7 w-7 text-danger" />
          </div>
          <h2 className="mb-2 text-xl font-semibold text-text">Access denied</h2>
          <p className="text-sm text-text-muted">
            You must be a member of the AI Society Discord server to access this platform.
          </p>
          <div className="mt-6 flex justify-center">
            <Button variant="secondary" onClick={handleSignOut}>
              Sign out
            </Button>
          </div>
        </div>
        <Toaster />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-4xl">
          <div className="mb-12 text-center">
            <div className="mb-6 flex items-center justify-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent">
                <Zap className="h-7 w-7 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-text">Godfather</h1>
            </div>
            <p className="mb-2 text-lg text-text-secondary">AI Society ASU Development Platform</p>
            <p className="mx-auto max-w-2xl text-sm text-text-muted">
              GPU compute for AI and machine learning projects, provisioned on managed RunPod
              environments and shared with your team.
            </p>
          </div>

          <div className="mb-12 grid gap-6 md:grid-cols-3">
            <div className="glass rounded-xl p-6 transition-colors hover:border-accent-border">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-accent-soft">
                <Cpu className="h-5 w-5 text-accent" />
              </div>
              <h3 className="mb-1 font-semibold text-text">GPU computing</h3>
              <p className="text-sm text-text-muted">Access NVIDIA GPUs for training and inference</p>
            </div>

            <div className="glass rounded-xl p-6 transition-colors hover:border-accent-border">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-accent-soft">
                <ShieldCheck className="h-5 w-5 text-accent" />
              </div>
              <h3 className="mb-1 font-semibold text-text">Secure access</h3>
              <p className="text-sm text-text-muted">Discord-based authentication for team members</p>
            </div>

            <div className="glass rounded-xl p-6 transition-colors hover:border-accent-border">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-accent-soft">
                <Terminal className="h-5 w-5 text-accent" />
              </div>
              <h3 className="mb-1 font-semibold text-text">CLI tool</h3>
              <p className="text-sm text-text-muted">Connect to pods from the terminal</p>
            </div>
          </div>

          <div className="glass rounded-2xl p-8">
            <div className="mb-6 text-center">
              <h2 className="mb-1 text-xl font-semibold text-text">Get started</h2>
              <p className="text-sm text-text-muted">Sign in with your Discord account to access the platform</p>
            </div>

            <div className="mb-6 flex justify-center">
              {!session ? (
                <Button size="lg" onClick={handleSignIn} className="w-full max-w-md">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                  <span>Sign in with Discord</span>
                </Button>
              ) : (
                <Button variant="secondary" onClick={handleSignOut}>
                  Sign out
                </Button>
              )}
            </div>

            <p className="text-center text-xs text-text-muted">For AI Society ASU Discord members</p>
          </div>

          <div className="mt-8 text-center text-xs text-text-muted">
            <p>Built by AI Society at Arizona State University</p>
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
}
