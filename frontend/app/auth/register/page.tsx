"use client";

import React, { useEffect } from "react";
import { RegisterForm } from "../../../components/AuthForms";
import { useAuth } from "../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Layout from "../../../components/Layout";

export default function Register() {
  const { user } = useAuth();
  const router = useRouter();

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      if (user.role === "hiring_manager") {
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
          <RegisterForm />
          <div className="mt-4 text-center">
            <p className="text-gray-600">
              Already have an account?{" "}
              <Link
                href="/auth/login"
                className="text-blue-500 hover:text-blue-700"
              >
                Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
