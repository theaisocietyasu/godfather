'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import toast, { Toaster } from 'react-hot-toast';
import { Copy, Check, Terminal, ShieldAlert, Crown, UserRound } from 'lucide-react';
import { verifyDiscordUser } from '@/features/auth/api';
import { LoadingScreen } from '@/components/Skeleton';
import { Card, CardBody } from '@/components/Card';
import Button from '@/components/Button';

export default function CliAuthView() {
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
        const data = await verifyDiscordUser(session.user.discordId);
        setIsAdmin(data.is_admin || false);

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
      toast.success('Token copied to clipboard');
      setTimeout(() => setCopied(false), 3000);
    } catch (error) {
      console.error('Error copying token:', error);
      toast.error('Failed to copy token');
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-bg">
      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
        <Card>
          <CardBody>
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-accent-soft">
                <Terminal className="h-6 w-6 text-accent" />
              </div>
              <h2 className="text-xl font-semibold text-text">CLI authentication token</h2>
            </div>

            <div className="space-y-6">
              <div className="rounded-lg border border-info/30 bg-info-soft p-4">
                <h3 className="mb-2 text-sm font-semibold text-info">How to use it</h3>
                <ol className="list-decimal space-y-1 pl-4 text-sm text-text-secondary">
                  <li>Copy the token below</li>
                  <li>
                    Run the CLI: <code className="rounded bg-bg-elevated px-1.5 py-0.5 text-text">godfather</code>
                  </li>
                  <li>Paste the token when prompted for authentication</li>
                  <li>
                    {isAdmin
                      ? 'You will have full admin access to manage all pods'
                      : 'You will have access to view and connect to available pods'}
                  </li>
                </ol>
              </div>

              {isAdmin ? (
                <div className="flex items-center gap-3 rounded-lg border border-accent-border bg-accent-soft p-4">
                  <Crown className="h-5 w-5 text-accent" />
                  <div>
                    <h3 className="text-sm font-semibold text-text">Admin access</h3>
                    <p className="text-sm text-text-muted">Full administrative privileges</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-lg border border-success/30 bg-success-soft p-4">
                  <UserRound className="h-5 w-5 text-success" />
                  <div>
                    <h3 className="text-sm font-semibold text-text">Member access</h3>
                    <p className="text-sm text-text-muted">View and connect to available pods</p>
                  </div>
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-medium text-text-secondary">
                  Your authentication token
                </label>
                <div className="relative">
                  <textarea
                    readOnly
                    value={token}
                    className="w-full resize-none rounded-lg border border-border bg-bg-elevated px-4 py-3 pr-12 font-mono text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent"
                    rows={6}
                    onClick={(e) => e.currentTarget.select()}
                  />
                  <button
                    onClick={copyToken}
                    className="absolute right-2 top-2 rounded-md border border-border bg-surface p-2 hover:bg-surface-hover"
                    title="Copy token"
                  >
                    {copied ? <Check className="h-5 w-5 text-success" /> : <Copy className="h-5 w-5 text-text-secondary" />}
                  </button>
                </div>
                <p className="mt-2 text-xs text-text-muted">
                  This token expires after a period of time. If you get authentication errors, come back here for a
                  fresh one.
                </p>
              </div>

              <Button onClick={copyToken} className="w-full">
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    <span>Copy token</span>
                  </>
                )}
              </Button>

              <div className="rounded-lg border border-border bg-bg-elevated p-4 font-mono text-sm">
                <div className="mb-2 text-text-muted"># Example CLI usage</div>
                <div className="space-y-1">
                  <div className="text-success">$ godfather</div>
                  <div className="text-text">What would you like to do?</div>
                  <div className="text-text-secondary">  1. List available pods</div>
                  <div className="text-text-secondary">  2. Connect to a pod</div>
                  <div className="text-text-secondary">  3. Show status</div>
                  <div className="text-text-secondary">  4. Logout</div>
                  <div className="text-text-secondary">  5. Exit</div>
                  <div className="mt-2 text-success">Enter your choice (1-5): 1</div>
                  <div className="text-text">Fetching available pods...</div>
                  <div className="text-warning">Authentication required</div>
                  <div className="text-text">
                    Enter your authentication token: <span className="text-text-muted">[paste token here]</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-warning/30 bg-warning-soft p-4">
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-warning">
                  <ShieldAlert className="h-4 w-4" />
                  Security notice
                </h3>
                <ul className="list-disc space-y-1 pl-4 text-sm text-text-secondary">
                  <li>Keep this token secure, it grants access to your account</li>
                  <li>Do not share this token with anyone</li>
                  <li>Do not commit this token to version control</li>
                  <li>Tokens expire automatically</li>
                </ul>
              </div>
            </div>
          </CardBody>
        </Card>
      </main>

      <Toaster />
    </div>
  );
}
