"use client";

import React, { useEffect } from "react";
import { LoginForm } from "../../../components/AuthForms";
import { useAuth } from "../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Layout from "../../../components/Layout";

export default function Login() {
  const { user } = useAuth();
  const router = useRouter();

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      if (user.role === "hiring_manager" || user.role === "admin") {
        router.push("/dashboard/hiring");
      } else {
        router.push("/dashboard/candidate");
      }
    }
  }, [user, router]);

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center py-12">
        <div className="w-full max-w-md">
          <LoginForm />
          <div className="mt-4 text-center">
            <p className="text-gray-600">
              Don&apos;t have an account?{" "}
              <Link
                href="/auth/register"
                className="text-blue-500 hover:text-blue-700"
              >
                Register
              </Link>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
