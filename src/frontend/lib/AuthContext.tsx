import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { apiClient } from "./api";

// Define user type
interface User {
  email: string;
  name: string;
  role: "hiring_manager" | "candidate" | "admin";
  profile_id?: string;
}

// Define auth context type
interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    name: string,
    email: string,
    password: string,
    role: "hiring_manager" | "candidate"
  ) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

// Create auth context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: false,
  error: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  updateUser: () => {},
});

// Custom hook for using auth context
export const useAuth = () => useContext(AuthContext);

// Auth provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      const token = localStorage.getItem("accessToken");

      if (token) {
        try {
          // Use the apiClient to get user profile
          const data = await apiClient.getUserProfile();
          setUser(data.user);
        } catch (err) {
          console.error("Authentication error:", err);
          localStorage.removeItem("accessToken");
        }
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  // Login function
  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      // Use the apiClient for login
      const data = await apiClient.login(email, password);
      localStorage.setItem("accessToken", data.access_token);
      setUser(data.user);
    } catch (err: any) {
      setError(err.message || "An error occurred during login");
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (
    name: string,
    email: string,
    password: string,
    role: "hiring_manager" | "candidate"
  ) => {
    setLoading(true);
    setError(null);

    try {
      // Use the apiClient for registration
      const data = await apiClient.register({ name, email, password, role });
      localStorage.setItem("accessToken", data.access_token);
      setUser(data.user);
    } catch (err: any) {
      setError(err.message || "An error occurred during registration");
      console.error("Registration error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem("accessToken");
    setUser(null);
  };

  // Update user data
  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
