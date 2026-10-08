export interface ApiErrorPayload {
  code: string;
  message: string | Record<string, any>;
  status: number;
  data?: Record<string, any>;
}

export class ApiError extends Error {
  code: string;
  status: number;
  data?: Record<string, any>;

  constructor(payload: ApiErrorPayload) {
    const msg =
      typeof payload.message === 'string'
        ? payload.message
        : JSON.stringify(payload.message);
    super(msg);
    this.name = 'ApiError';
    this.code = payload.code || 'api_error';
    this.status = payload.status || 400;
    this.data = payload.data;
  }
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || (typeof window !== 'undefined' ? '/api/v1' : 'http://localhost:8000/api/v1');
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private getCsrfToken(): string | null {
    if (typeof document === 'undefined') return null;
    const match = document.cookie.match(/(^|;)\s*edukit_csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[2]) : null;
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers = {}, ...rest } = options;

    let url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          searchParams.append(key, String(val));
        }
      });
      const qs = searchParams.toString();
      if (qs) url += `?${qs}`;
    }

    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    const csrf = this.getCsrfToken();
    if (csrf) {
      defaultHeaders['X-CSRFToken'] = csrf;
    }

    if (this.token) {
      defaultHeaders['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        ...defaultHeaders,
        ...(headers as Record<string, string>),
      },
      ...rest,
    });

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (data && data.error) {
        throw new ApiError(data.error);
      }
      throw new ApiError({
        code: `http_${response.status}`,
        message: data.detail || response.statusText || 'Request failed',
        status: response.status,
      });
    }

    return data as T;
  }

  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', ...options });
  }

  post<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  patch<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  put<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE', ...options });
  }
}

export const client = new ApiClient();
