export interface SensorData {
  temperature: number;
  humidity: number;
  pressure: number;
  timestamp: string;
}

export interface ImageData {
  id: string;
  url: string;
  thumbnail_url: string;
  timestamp: string;
}

export interface ImageUrls {
  original: string;
  large: string;
  medium: string;
  small: string;
  thumbnail: string;
  custom?: string;
}