"use client";

import React, { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../lib/AuthContext";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const isActive = (path: string) => {
    return pathname === path || pathname?.startsWith(`${path}/`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link href="/" className="text-xl font-bold text-blue-600">
                  TalentMatcher
                </Link>
              </div>
              <div className="ml-10 flex items-center space-x-4">
                <Link
                  href="/jobs"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    isActive("/jobs")
                      ? "bg-blue-100 text-blue-700"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  Jobs
                </Link>
                {user &&
                  (user.role === "hiring_manager" || user.role === "admin") && (
                    <Link
                      href="/candidates"
                      className={`px-3 py-2 rounded-md text-sm font-medium ${
                        isActive("/candidates")
                          ? "bg-blue-100 text-blue-700"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                      }`}
                    >
                      Candidates
                    </Link>
                  )}
                <Link
                  href="/skills"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    isActive("/skills")
                      ? "bg-blue-100 text-blue-700"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  Skills Library
                </Link>

                {user && user.role === "hiring_manager" && (
                  <Link
                    href="/dashboard/hiring"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive("/dashboard/hiring")
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    My Dashboard
                  </Link>
                )}

                {user && user.role === "candidate" && (
                  <Link
                    href="/dashboard/candidate"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive("/dashboard/candidate")
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    My Dashboard
                  </Link>
                )}
              </div>
            </div>

            <div className="flex items-center">
              {user ? (
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">
                    Welcome, {user.name}
                  </span>
                  <button
                    onClick={logout}
                    className="px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:text-red-900 hover:bg-red-50"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <Link
                    href="/auth/login"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive("/auth/login")
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    Login
                  </Link>
                  <Link
                    href="/auth/register"
                    className="px-3 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            &copy; {new Date().getFullYear()} TalentMatcher - Skill-based
            Matching Platform
          </p>
        </div>
      </footer>
    </div>
  );
}
