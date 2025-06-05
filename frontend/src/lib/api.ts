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

export const getImageStream = async (imageId: string): Promise<Blob> => {
  const response = await api.get(`/images/${imageId}/stream`, {
    responseType: 'blob',
  });
  return response.data;
}; 