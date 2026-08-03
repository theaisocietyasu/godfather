'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { signOut } from '@/lib/auth-client';
import {
  LayoutDashboard,
  Terminal,
  Plus,
  LogOut,
  User,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';
import Image from 'next/image';
import clsx from 'clsx';

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { data: session } = useSession();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'CLI Token', href: '/cli-auth', icon: Terminal },
  ];

  const isActive = (href: string) => pathname === href;

  const userAvatar = session?.user?.discordAvatar ? (
    <Image
      src={`https://cdn.discordapp.com/avatars/${session.user.discordId}/${session.user.discordAvatar}.png?size=32`}
      alt={session.user.discordUsername || 'User'}
      width={32}
      height={32}
      className="rounded-full ring-2 ring-accent-border"
    />
  ) : (
    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent">
      <User className="h-4 w-4 text-white" />
    </div>
  );

  return (
    <nav className="border-b border-border bg-bg-elevated/95 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <button onClick={() => router.push('/dashboard')} className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent">
                <LayoutDashboard className="h-5 w-5 text-white" />
              </div>
              <div className="flex flex-col leading-tight">
                <span className="text-base font-semibold text-text">Godfather</span>
                <span className="text-xs text-text-muted">AI Society ASU</span>
              </div>
            </button>

            <div className="hidden items-center gap-1 md:flex">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <button
                    key={item.name}
                    onClick={() => router.push(item.href)}
                    className={clsx(
                      'flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors',
                      active
                        ? 'bg-surface text-text'
                        : 'text-text-secondary hover:bg-surface hover:text-text'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="hidden items-center gap-3 md:flex">
            <button
              onClick={() => router.push('/dashboard/create-pod')}
              className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
            >
              <Plus className="h-4 w-4" />
              <span>New Pod</span>
            </button>

            <div className="flex items-center gap-3 rounded-lg border border-border bg-surface px-3 py-1.5">
              {userAvatar}
              <div className="flex flex-col leading-tight">
                <span className="text-sm font-medium text-text">
                  {session?.user?.name || session?.user?.discordUsername || 'User'}
                </span>
              </div>
            </div>

            <button
              onClick={() => signOut({ callbackUrl: '/' })}
              className="rounded-lg p-2 text-text-secondary transition-colors hover:bg-surface hover:text-text"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-text-secondary hover:bg-surface hover:text-text md:hidden"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="border-t border-border bg-bg-elevated md:hidden">
          <div className="space-y-2 px-4 py-4">
            <div className="mb-4 flex items-center gap-3 rounded-lg bg-surface px-4 py-3">
              {userAvatar}
              <span className="text-sm font-medium text-text">
                {session?.user?.name || session?.user?.discordUsername || 'User'}
              </span>
            </div>

            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    router.push(item.href);
                    setMobileMenuOpen(false);
                  }}
                  className={clsx(
                    'flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
                    active ? 'bg-surface text-text' : 'text-text-secondary hover:bg-surface hover:text-text'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </button>
              );
            })}

            <button
              onClick={() => {
                router.push('/dashboard/create-pod');
                setMobileMenuOpen(false);
              }}
              className="flex w-full items-center gap-3 rounded-lg bg-accent px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
            >
              <Plus className="h-5 w-5" />
              <span>New Pod</span>
            </button>

            <button
              onClick={() => signOut({ callbackUrl: '/' })}
              className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-text-secondary transition-colors hover:bg-surface hover:text-text"
            >
              <LogOut className="h-5 w-5" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
