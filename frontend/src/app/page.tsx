'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Tab } from '@headlessui/react';
import { CameraIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import SensorDisplay from '@/components/SensorDisplay';
import TimeLapse from '@/components/TimeLapse';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/images');
  }, [router]);

  const tabs = [
    { name: 'Time Lapse', icon: CameraIcon, component: TimeLapse },
    { name: 'Sensor Data', icon: ChartBarIcon, component: SensorDisplay },
  ];

  return null;
}
