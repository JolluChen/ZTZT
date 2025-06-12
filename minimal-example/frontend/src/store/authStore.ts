import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';
import { authService } from '@/services';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        try {
          set({ isLoading: true });
          const response = await authService.login({ username, password });
          
          // 保存token到localStorage
          localStorage.setItem('token', response.token);
          
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        // 清除localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // 调用后端logout API
        authService.logout().catch(() => {
          // 忽略logout错误
        });
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      setToken: (token: string) => {
        localStorage.setItem('token', token);
        set({ token, isAuthenticated: true });
      },

      refreshUser: async () => {
        try {
          const user = await authService.getProfile();
          set({ user });
        } catch (error) {
          // 如果获取用户信息失败，可能token已过期
          get().logout();
          throw error;
        }
      },

      hasPermission: (permission: string) => {
        const { user } = get();
        if (!user || !user.permissions) {
          return false;
        }
        
        // 如果用户是超级管理员，拥有所有权限
        if (user.permissions.includes('admin_super')) {
          return true;
        }
        
        // 检查是否拥有特定权限
        return user.permissions.includes(permission);
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
