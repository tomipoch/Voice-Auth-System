/**
 * Superadmin Service - System-wide Management
 * Servicio para gestionar funcionalidades exclusivas de superadmin
 */

import api from './api';

// =====================================================
// Types
// =====================================================

export interface CompanyStats {
  name: string;
  user_count: number;
  enrolled_count: number;
  admin_count: number;
  verification_count_30d: number;
  status: 'active' | 'inactive';
}

export interface GlobalStats {
  total_companies: number;
  total_users: number;
  total_enrollments: number;
  total_verifications: number;
  total_verifications_30d: number;
  success_rate: number;
  spoof_detection_rate: number;
  avg_latency_ms: number;
  storage_used_mb: number;
}

export interface SystemHealth {
  api_status: 'healthy' | 'degraded' | 'down';
  api_uptime_seconds: number;
  api_latency_ms: number;
  database_status: string;
  database_connections: number;
  database_max_connections: number;
  models_status: Record<string, string>;
  last_check: string;
}

export interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_usage_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  uptime_seconds: number;
  load_average_1m: number;
  load_average_5m: number;
  load_average_15m: number;
  process_count: number;
}

export interface ModelInfo {
  name: string;
  version: string;
  kind: 'speaker' | 'antispoof' | 'asr';
  status: 'loaded' | 'loading' | 'error' | 'not_loaded';
  load_time_ms?: number;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  company?: string;
  success: boolean;
  details?: string;
}

export interface ThresholdConfig {
  similarity_threshold: number;
  spoof_threshold: number;
  phrase_match_threshold: number;
  max_failed_attempts: number;
  lockout_duration_minutes: number;
}

export interface AuditLogFilters {
  limit?: number;
  action?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
}

export interface PurgeResult {
  success: boolean;
  message: string;
  executed_at: string;
}

// =====================================================
// Service
// =====================================================

class SuperadminService {
  private readonly baseUrl = '/superadmin';

  // =====================================================
  // System Health
  // =====================================================

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get<SystemHealth>(`${this.baseUrl}/system/health`);
    return response.data;
  }

  /**
   * Get real system metrics (CPU, memory, disk) from container
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await api.get<SystemMetrics>(`${this.baseUrl}/system/metrics`);
    return response.data;
  }

  // =====================================================
  // Statistics
  // =====================================================

  /**
   * Get global statistics across all companies
   */
  async getGlobalStats(): Promise<GlobalStats> {
    const response = await api.get<GlobalStats>(`${this.baseUrl}/stats/global`);
    return response.data;
  }

  /**
   * Get statistics broken down by company
   */
  async getStatsByCompany(): Promise<CompanyStats[]> {
    const response = await api.get<CompanyStats[]>(`${this.baseUrl}/stats/by-company`);
    return response.data;
  }

  // =====================================================
  // Companies
  // =====================================================

  /**
   * Get all companies with statistics
   */
  async getCompanies(): Promise<CompanyStats[]> {
    const response = await api.get<CompanyStats[]>(`${this.baseUrl}/companies`);
    return response.data;
  }

  // =====================================================
  // Audit Logs
  // =====================================================

  /**
   * Get global audit logs with optional filtering
   */
  async getAuditLogs(filters?: AuditLogFilters): Promise<AuditLogEntry[]> {
    const params = new URLSearchParams();
    
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.action) params.append('action', filters.action);
    if (filters?.company) params.append('company', filters.company);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await api.get<AuditLogEntry[]>(
      `${this.baseUrl}/audit?${params.toString()}`
    );
    return response.data;
  }

  // =====================================================
  // Models
  // =====================================================

  /**
   * Get status of all biometric models
   */
  async getModelsStatus(): Promise<ModelInfo[]> {
    const response = await api.get<ModelInfo[]>(`${this.baseUrl}/models`);
    return response.data;
  }

  // =====================================================
  // Configuration
  // =====================================================

  /**
   * Get current threshold configuration
   */
  async getThresholdConfig(): Promise<ThresholdConfig> {
    const response = await api.get<ThresholdConfig>(`${this.baseUrl}/config/thresholds`);
    return response.data;
  }

  // =====================================================
  // Maintenance
  // =====================================================

  /**
   * Execute data purge for expired audio and challenges
   */
  async runDataPurge(): Promise<PurgeResult> {
    const response = await api.post<PurgeResult>(`${this.baseUrl}/system/purge`);
    return response.data;
  }
}

export const superadminService = new SuperadminService();
export default superadminService;
