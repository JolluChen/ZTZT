// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  profile?: UserProfile;
  permissions?: string[];
}

export interface UserProfile {
  id: number;
  user: number;
  phone: string;
  department: string;
  position: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

// 数据中台相关类型
export interface Dataset {
  id: number;
  name: string;
  description: string;
  file_path: string;
  file_size: number;
  created_by: number;
  created_at: string;
  updated_at: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  tags: string[];
}

export interface DatasetCreateRequest {
  name: string;
  description: string;
  file: File;
  tags?: string[];
}

// 算法中台相关类型
export interface Experiment {
  id: number;
  name: string;
  description: string;
  algorithm: string;
  parameters: Record<string, unknown>;
  dataset: number;
  status: 'created' | 'running' | 'completed' | 'failed';
  created_by: number;
  created_at: string;
  updated_at: string;
  results: Record<string, unknown>;
}

export interface ExperimentCreateRequest {
  name: string;
  description: string;
  algorithm: string;
  parameters: Record<string, unknown>;
  dataset: number;
}

// 模型中台相关类型
export interface Model {
  id: number;
  name: string;
  description: string;
  algorithm: string;
  version: string;
  experiment: number;
  created_by: number;
  created_at: string;
  updated_at: string;
  status: 'training' | 'ready' | 'deployed' | 'archived';
  metrics: Record<string, unknown>;
}

export interface ModelCreateRequest {
  name: string;
  description: string;
  experiment: number;
  version?: string;
}

// 服务中台相关类型
export interface Application {
  id: number;
  name: string;
  description: string;
  model: number;
  status: 'created' | 'deploying' | 'running' | 'stopped' | 'error';
  url: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  config: Record<string, unknown>;
}

export interface ApplicationCreateRequest {
  name: string;
  description: string;
  model: number;
  config?: Record<string, unknown>;
}

// 通用API响应类型
export interface ApiResponse<T> {
  count?: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

// 菜单和导航类型
export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  children?: MenuItem[];
  path?: string;
  permission?: string;
}

// 表格列配置类型
export interface TableColumn {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  fixed?: 'left' | 'right';
  sorter?: boolean;
  filters?: { text: string; value: unknown }[];
  render?: (value: unknown, record: Record<string, unknown>) => React.ReactNode;
}

// 表单字段类型
export interface FormField {
  name: string;
  label: string;
  type: 'input' | 'textarea' | 'select' | 'upload' | 'number' | 'date';
  required?: boolean;
  options?: { label: string; value: unknown }[];
  placeholder?: string;
  rules?: Record<string, unknown>[];
}

// 统计数据类型
export interface StatItem {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  precision?: number;
}

// 图表数据类型
export interface ChartData {
  name: string;
  value: number;
  [key: string]: unknown;
}
