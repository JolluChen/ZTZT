import api from './api';
import { API_ENDPOINTS } from '@/constants';
import {
  LoginRequest,
  LoginResponse,
  User,
  UserProfile,
  Dataset,
  DatasetCreateRequest,
  Experiment,
  ExperimentCreateRequest,
  Model,
  ModelCreateRequest,
  Application,
  ApplicationCreateRequest,
  ApiResponse,
} from '@/types';

// 认证服务
export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    console.log('🔐 AuthService: 发送登录请求到:', API_ENDPOINTS.AUTH.LOGIN); // 调试日志
    console.log('🔐 AuthService: 请求数据:', credentials); // 调试日志
    
    const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, credentials);
    
    console.log('🔐 AuthService: 响应数据:', response.data); // 调试日志
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  async register(userData: Record<string, unknown>): Promise<User> {
    const response = await api.post(API_ENDPOINTS.AUTH.REGISTER, userData);
    return response.data;
  },

  async getProfile(): Promise<User> {
    const response = await api.get(API_ENDPOINTS.AUTH.PROFILE);
    return response.data;
  },

  async updateProfile(profileData: Partial<UserProfile>): Promise<UserProfile> {
    const response = await api.patch(API_ENDPOINTS.AUTH.PROFILE, profileData);
    return response.data;
  },

  async changePassword(passwordData: {
    old_password: string;
    new_password: string;
  }): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, passwordData);
  },
};

// 数据中台服务
export const dataService = {
  async getDatasets(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Dataset>> {
    const response = await api.get(API_ENDPOINTS.DATA.DATASETS, { params });
    return response.data;
  },

  async getDataset(id: number): Promise<Dataset> {
    const response = await api.get(`${API_ENDPOINTS.DATA.DATASETS}${id}/`);
    return response.data;
  },

  async createDataset(datasetData: DatasetCreateRequest): Promise<Dataset> {
    const formData = new FormData();
    formData.append('name', datasetData.name);
    formData.append('description', datasetData.description);
    formData.append('file', datasetData.file);
    if (datasetData.tags) {
      formData.append('tags', JSON.stringify(datasetData.tags));
    }

    const response = await api.post(API_ENDPOINTS.DATA.DATASETS, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async updateDataset(id: number, datasetData: Partial<Dataset>): Promise<Dataset> {
    const response = await api.patch(`${API_ENDPOINTS.DATA.DATASETS}${id}/`, datasetData);
    return response.data;
  },

  async deleteDataset(id: number): Promise<void> {
    await api.delete(`${API_ENDPOINTS.DATA.DATASETS}${id}/`);
  },

  async previewDataset(id: number): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.DATA.PREVIEW}${id}/`);
    return response.data;
  },

  async getDataStats(): Promise<any> {
    const response = await api.get(API_ENDPOINTS.DATA.STATS);
    return response.data;
  },

  async getDatasetStats(id: number): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.DATA.DATASETS}${id}/stats/`);
    return response.data;
  },

  async downloadDataset(id: number): Promise<void> {
    const response = await api.get(`${API_ENDPOINTS.DATA.DATASETS}${id}/download/`, {
      responseType: 'blob'
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `dataset_${id}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

// 算法中台服务
export const algorithmService = {
  async getExperiments(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Experiment>> {
    const response = await api.get(API_ENDPOINTS.ALGORITHM.EXPERIMENTS, { params });
    return response.data;
  },

  async getExperiment(id: number): Promise<Experiment> {
    const response = await api.get(`${API_ENDPOINTS.ALGORITHM.EXPERIMENTS}${id}/`);
    return response.data;
  },

  async createExperiment(experimentData: ExperimentCreateRequest): Promise<Experiment> {
    const response = await api.post(API_ENDPOINTS.ALGORITHM.EXPERIMENTS, experimentData);
    return response.data;
  },

  async runExperiment(id: number): Promise<Experiment> {
    const response = await api.post(`${API_ENDPOINTS.ALGORITHM.RUN}${id}/`);
    return response.data;
  },

  async getExperimentResults(id: number): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.ALGORITHM.RESULTS}${id}/`);
    return response.data;
  },

  async getAlgorithms(): Promise<any[]> {
    const response = await api.get(API_ENDPOINTS.ALGORITHM.ALGORITHMS);
    return response.data;
  },
};

// 模型中台服务
export const modelService = {
  async getModels(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Model>> {
    const response = await api.get(API_ENDPOINTS.MODEL.MODELS, { params });
    return response.data;
  },

  async getModel(id: number): Promise<Model> {
    const response = await api.get(`${API_ENDPOINTS.MODEL.MODELS}${id}/`);
    return response.data;
  },

  async createModel(modelData: ModelCreateRequest): Promise<Model> {
    const response = await api.post(API_ENDPOINTS.MODEL.MODELS, modelData);
    return response.data;
  },

  async updateModel(id: number, modelData: Partial<Model>): Promise<Model> {
    const response = await api.patch(`${API_ENDPOINTS.MODEL.MODELS}${id}/`, modelData);
    return response.data;
  },

  async deployModel(id: number, config?: Record<string, unknown>): Promise<Model> {
    const response = await api.post(`${API_ENDPOINTS.MODEL.DEPLOY}${id}/`, config || {});
    return response.data;
  },

  async getModelVersions(modelId: number): Promise<any[]> {
    const response = await api.get(`${API_ENDPOINTS.MODEL.VERSIONS}?model=${modelId}`);
    return response.data;
  },

  async getModelMetrics(id: number): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.MODEL.METRICS}${id}/`);
    return response.data;
  },

  async deleteModel(id: number): Promise<void> {
    await api.delete(`${API_ENDPOINTS.MODEL.MODELS}${id}/`);
  },

  // 获取实验列表（用于创建模型时选择）
  async getExperiments(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Experiment>> {
    const response = await api.get(API_ENDPOINTS.ALGORITHM.EXPERIMENTS, { params });
    return response.data;
  },
};

// 服务中台服务
export const serviceService = {
  async getApplications(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Application>> {
    const response = await api.get(API_ENDPOINTS.SERVICE.APPLICATIONS, { params });
    return response.data;
  },

  async getApplication(id: number): Promise<Application> {
    const response = await api.get(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/`);
    return response.data;
  },

  async createApplication(applicationData: ApplicationCreateRequest): Promise<Application> {
    const response = await api.post(API_ENDPOINTS.SERVICE.APPLICATIONS, applicationData);
    return response.data;
  },

  async updateApplication(id: number, applicationData: Partial<Application>): Promise<Application> {
    const response = await api.patch(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/`, applicationData);
    return response.data;
  },

  async deployApplication(id: number): Promise<Application> {
    const response = await api.post(`${API_ENDPOINTS.SERVICE.DEPLOY}${id}/`);
    return response.data;
  },

  async getApplicationStatus(id: number): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.SERVICE.STATUS}${id}/`);
    return response.data;
  },

  async getApplicationLogs(id: number, params?: { lines?: number; timeRange?: string }): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.SERVICE.LOGS}${id}/`, { params });
    return response.data;
  },

  async getApplicationMetrics(id: number, params?: { timeRange?: string }): Promise<any> {
    const response = await api.get(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/metrics/`, { params });
    return response.data;
  },

  async deleteApplication(id: number): Promise<void> {
    await api.delete(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/`);
  },

  async startApplication(id: number): Promise<Application> {
    const response = await api.post(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/start/`);
    return response.data;
  },

  async stopApplication(id: number): Promise<Application> {
    const response = await api.post(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/stop/`);
    return response.data;
  },

  async updateApplicationConfig(id: number, config: Record<string, unknown>): Promise<Application> {
    const response = await api.patch(`${API_ENDPOINTS.SERVICE.APPLICATIONS}${id}/`, { config });
    return response.data;
  },

  // 获取模型列表（用于创建应用时选择）
  async getModels(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
  }): Promise<ApiResponse<Model>> {
    const response = await api.get(API_ENDPOINTS.MODEL.MODELS, { params });
    return response.data;
  },
};
