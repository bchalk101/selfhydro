'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlayIcon, PauseIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';
import { ImageData } from '@/types';
import { getImages } from '@/lib/api';
import { format } from 'date-fns';
import Image from 'next/image';

export default function TimeLapse() {
  const [mounted, setMounted] = useState(false);
  const [images, setImages] = useState<ImageData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [speed, setSpeed] = useState(2000); // Default 2 seconds per image
  const [imageLoadStates, setImageLoadStates] = useState<Record<string, 'loading' | 'loaded' | 'error'>>({});
  const [mainImageLoaded, setMainImageLoaded] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const fetchImages = async () => {
      try {
        setLoading(true);
        const data = await getImages(24);
        setImages(data);
        if (data.length > 0) {
          setSelectedImage(data[0]);
          // Initialize loading states
          const initialStates: Record<string, 'loading' | 'loaded' | 'error'> = {};
          data.forEach(img => {
            initialStates[img.id] = 'loading';
          });
          setImageLoadStates(initialStates);
        }
      } catch (err) {
        console.error('Failed to fetch images:', err);
        setError('Failed to fetch images');
      } finally {
        setLoading(false);
      }
    };

    fetchImages();
  }, [mounted]);

  // Auto-play functionality with image loading wait
  useEffect(() => {
    if (!mounted || !isPlaying || images.length === 0) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % images.length;
        setSelectedImage(images[nextIndex]);
        setMainImageLoaded(false); // Reset loading state for next image
        return nextIndex;
      });
    }, speed);

    return () => clearInterval(interval);
  }, [isPlaying, images, mounted, speed]);

  // Scroll to active thumbnail
  const scrollToThumbnail = useCallback((index: number) => {
    if (!mounted || !scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const thumbnail = container.children[index] as HTMLElement;
    
    if (thumbnail) {
      const scrollLeft = thumbnail.offsetLeft - container.clientWidth / 2 + thumbnail.clientWidth / 2;
      container.scrollTo({ left: scrollLeft, behavior: 'smooth' });
    }
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    scrollToThumbnail(currentIndex);
  }, [currentIndex, mounted, scrollToThumbnail]);

  const handlePrevious = useCallback(() => {
    if (images.length === 0) return;
    setIsPlaying(false);
    setCurrentIndex((prev) => {
      const newIndex = prev > 0 ? prev - 1 : images.length - 1;
      setSelectedImage(images[newIndex]);
      setMainImageLoaded(false);
      return newIndex;
    });
  }, [images]);

  const handleNext = useCallback(() => {
    if (images.length === 0) return;
    setIsPlaying(false);
    setCurrentIndex((prev) => {
      const newIndex = (prev + 1) % images.length;
      setSelectedImage(images[newIndex]);
      setMainImageLoaded(false);
      return newIndex;
    });
  }, [images]);

  const handleImageSelect = useCallback((image: ImageData, index: number) => {
    setSelectedImage(image);
    setCurrentIndex(index);
    setIsPlaying(false);
    setMainImageLoaded(false);
  }, []);

  const handleThumbnailLoad = useCallback((imageId: string) => {
    setImageLoadStates(prev => ({
      ...prev,
      [imageId]: 'loaded'
    }));
  }, []);

  const handleThumbnailError = useCallback((imageId: string) => {
    setImageLoadStates(prev => ({
      ...prev,
      [imageId]: 'error'
    }));
  }, []);

  const handleMainImageLoad = useCallback(() => {
    setMainImageLoaded(true);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    if (!mounted) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          handlePrevious();
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleNext();
          break;
        case ' ':
          e.preventDefault();
          setIsPlaying(prev => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [mounted, handlePrevious, handleNext]);

  if (!mounted || loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="aspect-video bg-gray-200 rounded-lg mb-6"></div>
          <div className="flex space-x-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="w-24 aspect-video bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="p-4 bg-red-100 text-red-700 rounded-lg">
          {error}
          <button 
            onClick={() => window.location.reload()} 
            className="ml-4 text-red-800 underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">No images available</p>
        </div>
      </div>
    );
  }

  const speedOptions = [
    { label: '0.5x', value: 4000 },
    { label: '1x', value: 2000 },
    { label: '2x', value: 1000 },
    { label: '4x', value: 500 },
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Time Lapse</h2>
        {selectedImage && (
          <p className="text-gray-500">
            Captured: {format(new Date(selectedImage.timestamp), 'PPpp')}
          </p>
        )}
      </div>

      {/* Main Image Display */}
      <div className="relative aspect-video mb-6 bg-gray-900 rounded-lg overflow-hidden">
        {/* Loading overlay for main image */}
        {!mainImageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-200 z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}
        
        <AnimatePresence mode="wait">
          {selectedImage && (
            <motion.div
              key={selectedImage.id}
              className="w-full h-full relative"
              initial={{ opacity: 0 }}
              animate={{ opacity: mainImageLoaded ? 1 : 0.3 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Image
                src={selectedImage.url}
                alt={`Plant at ${selectedImage.timestamp}`}
                className="object-contain"
                fill
                priority={currentIndex < 3}
                unoptimized
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1280px"
                onLoad={handleMainImageLoad}
                onError={() => {
                  console.error(`Failed to load main image: ${selectedImage.id}`);
                  setMainImageLoaded(true); // Show something even if failed
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            disabled={images.length === 0}
          >
            {isPlaying ? (
              <>
                <PauseIcon className="h-5 w-5 mr-2" />
                Pause
              </>
            ) : (
              <>
                <PlayIcon className="h-5 w-5 mr-2" />
                Play
              </>
            )}
          </button>

          {/* Speed Control */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Speed:</span>
            <select
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded text-sm bg-white"
            >
              {speedOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="text-sm text-gray-500 hidden sm:flex items-center">
            Use arrow keys or spacebar to control
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={handlePrevious}
            className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 transition-colors"
            disabled={images.length === 0}
          >
            <ChevronLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <span className="text-gray-600 min-w-[80px] text-center font-medium">
            {currentIndex + 1} / {images.length}
          </span>
          <button
            onClick={handleNext}
            className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 transition-colors"
            disabled={images.length === 0}
          >
            <ChevronRightIcon className="h-6 w-6 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Thumbnail Strip */}
      <div className="relative">
        <div
          ref={scrollContainerRef}
          className="flex space-x-2 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-thin"
        >
          {images.map((image, index) => {
            const loadState = imageLoadStates[image.id] || 'loading';
            return (
              <button
                key={image.id}
                onClick={() => handleImageSelect(image, index)}
                className={`relative flex-shrink-0 w-24 aspect-video snap-center rounded-md overflow-hidden transition-all duration-200 ${
                  selectedImage?.id === image.id
                    ? 'ring-2 ring-indigo-600 scale-105'
                    : 'hover:ring-2 hover:ring-indigo-400 hover:scale-105'
                }`}
              >
                {/* Thumbnail loading state */}
                {loadState === 'loading' && (
                  <div className="absolute inset-0 bg-gray-200 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                  </div>
                )}
                
                {/* Thumbnail error state */}
                {loadState === 'error' && (
                  <div className="absolute inset-0 bg-gray-300 flex items-center justify-center">
                    <span className="text-gray-500 text-xs">Error</span>
                  </div>
                )}

                {/* Thumbnail image */}
                <Image
                  src={image.thumbnail_url}
                  alt={`Thumbnail ${index + 1}`}
                  className={`w-full h-full object-cover transition-opacity ${
                    loadState === 'loaded' ? 'opacity-100' : 'opacity-0'
                  }`}
                  width={128}
                  height={72}
                  unoptimized
                  onLoad={() => handleThumbnailLoad(image.id)}
                  onError={() => handleThumbnailError(image.id)}
                />
                
                <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 transition-opacity" />
                
                {/* Timestamp overlay for thumbnails */}
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 text-center opacity-0 hover:opacity-100 transition-opacity">
                  {format(new Date(image.timestamp), 'HH:mm')}
                </div>

                {/* Loading indicator for current thumbnail */}
                {selectedImage?.id === image.id && !mainImageLoaded && (
                  <div className="absolute top-1 right-1">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Progress indicator */}
      {isPlaying && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-1">
            <div 
              className="bg-indigo-600 h-1 rounded-full transition-all duration-1000"
              style={{ width: `${((currentIndex + 1) / images.length) * 100}%` }}
            />
          </div>
          <div className="text-center mt-2 text-sm text-gray-500">
            Auto-playing at {speedOptions.find(s => s.value === speed)?.label} speed
          </div>
        </div>
      )}
    </div>
  );
}