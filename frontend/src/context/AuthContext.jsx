import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import AxiosInstance from '../components/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('coordinator_token'));
  const [email, setEmail] = useState(() => localStorage.getItem('coordinator_email'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    AxiosInstance.get('auth/session/', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (res.data?.authenticated) {
          setEmail(res.data.email || email);
        } else {
          logout();
        }
      })
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, []);

  const login = async (credentials) => {
    const res = await AxiosInstance.post('auth/login/', credentials);
    const nextToken = res.data.token;
    localStorage.setItem('coordinator_token', nextToken);
    localStorage.setItem('coordinator_email', res.data.email);
    setToken(nextToken);
    setEmail(res.data.email);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('coordinator_token');
    localStorage.removeItem('coordinator_email');
    setToken(null);
    setEmail(null);
  };

  const value = useMemo(
    () => ({ token, email, loading, login, logout, isAuthenticated: Boolean(token) }),
    [token, email, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
