import { useEffect, useState } from 'react';
import { SensorData } from '@/types';
import { getLatestSensorData, getSensorHistory } from '@/lib/api';
import { format } from 'date-fns';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function SensorDisplay() {
  const [currentData, setCurrentData] = useState<SensorData | null>(null);
  const [historicalData, setHistoricalData] = useState<SensorData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [current, history] = await Promise.all([
          getLatestSensorData(),
          getSensorHistory(24)
        ]);
        setCurrentData(current);
        setHistoricalData(history);
      } catch (err) {
        setError('Failed to fetch sensor data');
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        {error}
      </div>
    );
  }

  if (!currentData) {
    return (
      <div className="animate-pulse p-4">
        <div className="h-32 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  const currentMetrics = [
    {
      name: 'Temperature',
      value: currentData.temperature,
      unit: '°C',
      color: '#ef4444',
    },
    {
      name: 'Humidity',
      value: currentData.humidity,
      unit: '%',
      color: '#3b82f6',
    },
    {
      name: 'Pressure',
      value: currentData.pressure,
      unit: 'hPa',
      color: '#10b981',
    },
  ];

  const chartData = historicalData.map(data => ({
    timestamp: format(new Date(data.timestamp), 'HH:mm'),
    temperature: data.temperature,
    humidity: data.humidity,
    pressure: data.pressure,
  })).reverse();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Current Conditions</h2>
        <p className="text-gray-500">
          Last updated: {format(new Date(currentData.timestamp), 'PPpp')}
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {currentMetrics.map((item) => (
          <div
            key={item.name}
            className="p-4 rounded-lg border border-gray-200"
            style={{ borderLeftColor: item.color, borderLeftWidth: '4px' }}
          >
            <div className="text-sm text-gray-500">{item.name}</div>
            <div className="text-2xl font-bold">
              {item.value.toFixed(1)}{item.unit}
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        <div className="h-64">
          <h3 className="text-lg font-semibold mb-2">Temperature History (°C)</h3>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="temperature"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="h-64">
          <h3 className="text-lg font-semibold mb-2">Humidity History (%)</h3>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="humidity"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="h-64">
          <h3 className="text-lg font-semibold mb-2">Pressure History (hPa)</h3>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="pressure"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
} 