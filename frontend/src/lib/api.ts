import axios from 'axios';
import { SensorData, ImageData } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getLatestSensorData = async (): Promise<SensorData> => {
  const response = await api.get<SensorData>('/sensor/latest');
  return response.data;
};

export const getSensorHistory = async (limit: number = 24): Promise<SensorData[]> => {
  const response = await api.get<SensorData[]>(`/sensor/history?limit=${limit}`);
  return response.data;
};

export const getImages = async (limit: number = 24): Promise<ImageData[]> => {
  const response = await api.get<ImageData[]>(`/images?limit=${limit}`);
  return response.data;
};

interface ImageStreamOptions {
  width?: number;
  height?: number;
  quality?: number;
}

export const getImageStream = async (imageId: string, options: ImageStreamOptions = {}): Promise<Blob> => {
  const params = new URLSearchParams();
  if (options.width) params.append('width', options.width.toString());
  if (options.height) params.append('height', options.height.toString());
  if (options.quality) params.append('quality', options.quality.toString());
  
  const url = `/images/${imageId}/stream${params.toString() ? '?' + params.toString() : ''}`;
  const response = await api.get(url, {
    responseType: 'blob'
  });
  return response.data;
}; 