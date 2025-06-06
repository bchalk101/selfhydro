import axios, { AxiosInstance, AxiosError } from 'axios';
import { SensorData, ImageData, ImageUrls } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with better defaults
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Accept': 'application/json',
  },
});

// Add request interceptor for logging (only in development)
if (process.env.NODE_ENV === 'development') {
  api.interceptors.request.use(
    (config) => {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('API Request Error:', error);
      return Promise.reject(error);
    }
  );
}

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('API Response Error:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url,
        message: error.message
      });
    }
    
    // Handle specific error cases
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout - server is taking too long to respond');
    }
    
    if (error.response?.status === 404) {
      throw new Error('Resource not found');
    }
    
    if (error.response?.status === 503) {
      throw new Error('Service temporarily unavailable');
    }
    
    if (error.response?.status && error.response?.status >= 500) {
      throw new Error('Server error - please try again later');
    }
    
    throw error;
  }
);

export const getLatestSensorData = async (): Promise<SensorData> => {
  try {
    const response = await api.get<SensorData>('/sensor/latest');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch latest sensor data:', error);
    throw new Error('Failed to fetch sensor data');
  }
};

export const getSensorHistory = async (limit: number = 24): Promise<SensorData[]> => {
  try {
    const response = await api.get<SensorData[]>(`/sensor/history?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch sensor history:', error);
    throw new Error('Failed to fetch sensor history');
  }
};

export const getImages = async (limit: number = 24): Promise<ImageData[]> => {
  try {
    const response = await api.get<ImageData[]>(`/images?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch images:', error);
    throw new Error('Failed to fetch images');
  }
};

interface ImageUrlOptions {
  width?: number;
  height?: number;
  quality?: number;
}

export const getImageUrls = async (imageId: string, options: ImageUrlOptions = {}): Promise<ImageUrls> => {
  try {
    const params = new URLSearchParams();
    if (options.width) params.append('width', options.width.toString());
    if (options.height) params.append('height', options.height.toString());
    if (options.quality) params.append('quality', options.quality.toString());
    
    const url = `/images/${imageId}/urls${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<ImageUrls>(url);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch URLs for image ${imageId}:`, error);
    throw new Error(`Failed to get image URLs: ${imageId}`);
  }
};

// Utility function to preload an image from URL
export const preloadImage = (url: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve();
    img.onerror = () => reject(new Error(`Failed to preload image: ${url}`));
    img.src = url;
  });
};

// Preload multiple images
export const preloadImages = async (urls: string[]): Promise<void> => {
  try {
    await Promise.allSettled(urls.map(url => preloadImage(url)));
  } catch (error) {
    // Ignore preload errors, they shouldn't break the app
    console.warn('Some images failed to preload:', error);
  }
};

export const refreshImageUrls = async (imageId: string): Promise<ImageUrls> => {
  return getImageUrls(imageId, { quality: 85 }); // Fresh URLs
};