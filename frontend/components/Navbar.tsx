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
  X
} from 'lucide-react';
import { useState } from 'react';
import Image from 'next/image';

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

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-8">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center space-x-3 group"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-purple-500 rounded-lg blur-sm opacity-75 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg p-2">
                  <LayoutDashboard className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-white">Godfather</span>
                <span className="text-xs text-gray-400">by AI Society</span>
              </div>
            </button>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <button
                    key={item.name}
                    onClick={() => router.push(item.href)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                      active
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Side Actions */}
          <div className="hidden md:flex items-center space-x-3">
            {/* Create Pod Button */}
            <button
              onClick={() => router.push('/dashboard/create-pod')}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl"
            >
              <Plus className="w-4 h-4" />
              <span>Create Pod</span>
            </button>

            {/* User Menu */}
            <div className="flex items-center space-x-3 px-4 py-2 bg-gray-800 rounded-lg">
              {session?.user?.discordAvatar ? (
                <Image
                  src={`https://cdn.discordapp.com/avatars/${session.user.discordId}/${session.user.discordAvatar}.png?size=32`}
                  alt={session.user.discordUsername || 'User'}
                  width={32}
                  height={32}
                  className="rounded-full ring-2 ring-purple-500"
                />
              ) : (
                <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">
                  {session?.user?.name || session?.user?.discordUsername || 'User'}
                </span>
                <span className="text-xs text-gray-400">Godfather Role</span>
              </div>
            </div>

            {/* Sign Out */}
            <button
              onClick={() => signOut({ callbackUrl: '/' })}
              className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-all"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-800 bg-gray-900">
          <div className="px-4 py-4 space-y-2">
            {/* User Info */}
            <div className="flex items-center space-x-3 px-4 py-3 bg-gray-800 rounded-lg mb-4">
              {session?.user?.discordAvatar ? (
                <Image
                  src={`https://cdn.discordapp.com/avatars/${session.user.discordId}/${session.user.discordAvatar}.png?size=32`}
                  alt={session.user.discordUsername || 'User'}
                  width={32}
                  height={32}
                  className="rounded-full ring-2 ring-purple-500"
                />
              ) : (
                <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">
                  {session?.user?.name || session?.user?.discordUsername || 'User'}
                </span>
                <span className="text-xs text-gray-400">Godfather Role</span>
              </div>
            </div>

            {/* Navigation Links */}
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
                  className={`flex items-center space-x-3 w-full px-4 py-3 rounded-lg font-medium transition-all ${
                    active
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </button>
              );
            })}

            {/* Create Pod */}
            <button
              onClick={() => {
                router.push('/dashboard/create-pod');
                setMobileMenuOpen(false);
              }}
              className="flex items-center space-x-3 w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all"
            >
              <Plus className="w-5 h-5" />
              <span>Create Pod</span>
            </button>

            {/* Sign Out */}
            <button
              onClick={() => signOut({ callbackUrl: '/' })}
              className="flex items-center space-x-3 w-full px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-all"
            >
              <LogOut className="w-5 h-5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
