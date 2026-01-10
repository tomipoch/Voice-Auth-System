import api from './api';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
    company: string;
  };
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  company: string;
}

export const authService = {
  async login(email: string, password: string): Promise<User> {
    const response = await api.post<LoginResponse>('/auth/login', {
      email,
      password,
    });
    
    const { access_token, user } = response.data;
    
    // Store token and user info
    localStorage.setItem('bank_token', access_token);
    localStorage.setItem('bank_user', JSON.stringify(user));
    
    return user;
  },

  logout(): void {
    localStorage.removeItem('bank_token');
    localStorage.removeItem('bank_user');
  },

  getUser(): User | null {
    const userStr = localStorage.getItem('bank_user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('bank_token');
  },
};

export default authService;
