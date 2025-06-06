import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CameraIcon, ChartBarIcon } from '@heroicons/react/24/outline';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function Navigation() {
  const pathname = usePathname();
  
  const navigation = [
    { name: 'Time Lapse', href: '/images', icon: CameraIcon },
    { name: 'Sensor Data', href: '/sensors', icon: ChartBarIcon },
  ];

  return (
    <nav className="flex space-x-1 rounded-xl bg-white p-1 shadow-sm mb-6">
      {navigation.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.name}
            href={item.href}
            className={classNames(
              'w-full rounded-lg py-3 px-4 text-sm font-medium leading-5',
              'ring-white ring-opacity-60 ring-offset-2 ring-offset-indigo-400 focus:outline-none focus:ring-2',
              isActive
                ? 'bg-indigo-600 text-white shadow'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            )}
          >
            <div className="flex items-center justify-center space-x-2">
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </div>
          </Link>
        );
      })}
    </nav>
  );
} 