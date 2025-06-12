import { create } from 'zustand';

interface AppState {
  // 主题设置
  theme: 'light' | 'dark';
  collapsed: boolean;
  
  // 加载状态
  loading: boolean;
  
  // 全局消息
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message?: string;
    timestamp: number;
  }>;
  
  // Actions
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setCollapsed: (collapsed: boolean) => void;
  setLoading: (loading: boolean) => void;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  theme: 'light',
  collapsed: false,
  loading: false,
  notifications: [],

  setTheme: (theme) => {
    set({ theme });
    // 同步到localStorage
    localStorage.setItem('theme', theme);
  },

  toggleSidebar: () => {
    set((state) => ({ collapsed: !state.collapsed }));
  },

  setCollapsed: (collapsed) => {
    set({ collapsed });
  },

  setLoading: (loading) => {
    set({ loading });
  },

  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const timestamp = Date.now();
    
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id, timestamp }
      ].slice(-10) // 只保留最新10条通知
    }));
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter(n => n.id !== id)
    }));
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },
}));
