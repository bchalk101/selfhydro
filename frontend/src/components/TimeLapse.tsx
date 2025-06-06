'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlayIcon, PauseIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';
import { ImageData } from '@/types';
import { getImages, getImageStream } from '@/lib/api';
import { format } from 'date-fns';
import Image from 'next/image';

export default function TimeLapse() {
  const [mounted, setMounted] = useState(false);
  const [images, setImages] = useState<ImageData[]>([]);
  const [imageBlobs, setImageBlobs] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [windowWidth, setWindowWidth] = useState(0);
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [lowResImages, setLowResImages] = useState<Record<string, string>>({});

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const fetchImages = async () => {
      try {
        const data = await getImages(24);
        setImages(data);
        if (data.length > 0) {
          setSelectedImage(data[0]);
        }
      } catch {
        setError('Failed to fetch images');
      }
    };

    fetchImages();
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    // Set initial width
    handleResize();
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [mounted]);

  const loadImageBlob = useCallback(async (image: ImageData, isThumbnail: boolean = false) => {
    if (!imageBlobs[image.id] && !loadingStates[image.id]) {
      try {
        setLoadingStates(prev => ({ ...prev, [image.id]: true }));

        // First load a very low-res preview for immediate display
        if (!isThumbnail && !lowResImages[image.id]) {
          const lowResBlob = await getImageStream(image.id, { width: 320, quality: 30 });
          const lowResUrl = URL.createObjectURL(lowResBlob);
          setLowResImages(prev => ({ ...prev, [image.id]: lowResUrl }));
        }

        let options;
        if (isThumbnail) {
          options = { width: 96, quality: 60 };
        } else {
          // Responsive image sizes based on screen width
          if (windowWidth <= 640) { // Mobile
            options = { width: 640, quality: 75 };
          } else if (windowWidth <= 1024) { // Tablet
            options = { width: 1024, quality: 80 };
          } else { // Desktop
            options = { width: 1280, quality: 85 };
          }
        }
        
        const blob = await getImageStream(image.id, options);
        const url = URL.createObjectURL(blob);
        setImageBlobs(prev => ({ ...prev, [image.id]: url }));
        setLoadingStates(prev => ({ ...prev, [image.id]: false }));
      } catch (error) {
        console.error(`Failed to load image ${image.id}:`, error);
        setLoadingStates(prev => ({ ...prev, [image.id]: false }));
      }
    }
  }, [imageBlobs, loadingStates, lowResImages, windowWidth]);

  useEffect(() => {
    if (!mounted) return;

    if (selectedImage) {
      loadImageBlob(selectedImage, false);
    }

    // Preload next few images as thumbnails first
    const preloadCount = 5;
    const nextImages = images.slice(currentIndex + 1, currentIndex + preloadCount + 1);
    nextImages.forEach(image => loadImageBlob(image, true));
  }, [selectedImage, currentIndex, images, mounted, imageBlobs, loadImageBlob]);

  useEffect(() => {
    if (!mounted) return;
    return () => {
      Object.values(imageBlobs).forEach(URL.revokeObjectURL);
      Object.values(lowResImages).forEach(URL.revokeObjectURL);
    };
  }, [mounted, imageBlobs, lowResImages]);

  useEffect(() => {
    if (!mounted) return;
    let interval: NodeJS.Timeout;

    if (isPlaying && images.length > 0) {
      interval = setInterval(() => {
        setCurrentIndex((prevIndex) => {
          const nextIndex = (prevIndex + 1) % images.length;
          setSelectedImage(images[nextIndex]);
          return nextIndex;
        });
      }, 1000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isPlaying, images, mounted]);

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

  const handlePrevious = () => {
    setIsPlaying(false);
    setCurrentIndex((prev) => {
      const newIndex = prev > 0 ? prev - 1 : images.length - 1;
      setSelectedImage(images[newIndex]);
      return newIndex;
    });
  };

  const handleNext = () => {
    setIsPlaying(false);
    setCurrentIndex((prev) => {
      const newIndex = (prev + 1) % images.length;
      setSelectedImage(images[newIndex]);
      return newIndex;
    });
  };

  if (!mounted) {
    return (
      <div className="animate-pulse p-4">
        <div className="h-96 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        {error}
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="animate-pulse p-4">
        <div className="h-96 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

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

      <div className="relative aspect-video mb-6 bg-black rounded-lg overflow-hidden">
        <AnimatePresence mode="wait">
          {selectedImage && (imageBlobs[selectedImage.id] || lowResImages[selectedImage.id]) && (
            <motion.div
              key={selectedImage.id}
              className="w-full h-full relative"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Image
                src={imageBlobs[selectedImage.id] || lowResImages[selectedImage.id]}
                alt={`Plant at ${selectedImage.timestamp}`}
                className={`object-contain transition-opacity duration-300 ${
                  loadingStates[selectedImage.id] ? 'opacity-50' : 'opacity-100'
                } ${lowResImages[selectedImage.id] && !imageBlobs[selectedImage.id] ? 'blur-sm' : ''}`}
                fill
                unoptimized
                priority
              />
              {loadingStates[selectedImage.id] && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex justify-between items-center mb-6">
        <div className="flex space-x-4">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
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
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={handlePrevious}
            className="p-2 rounded-full hover:bg-gray-100"
          >
            <ChevronLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <span className="text-gray-600 min-w-[80px] text-center">
            {currentIndex + 1} / {images.length}
          </span>
          <button
            onClick={handleNext}
            className="p-2 rounded-full hover:bg-gray-100"
          >
            <ChevronRightIcon className="h-6 w-6 text-gray-600" />
          </button>
        </div>
      </div>

      <div className="relative">
        <div
          ref={scrollContainerRef}
          className="flex space-x-2 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
        >
          {images.map((image, index) => (
            <button
              key={image.id}
              onClick={() => {
                setSelectedImage(image);
                setCurrentIndex(index);
                setIsPlaying(false);
              }}
              className={`relative flex-shrink-0 w-24 aspect-video snap-center ${
                selectedImage?.id === image.id
                  ? 'ring-2 ring-indigo-600'
                  : 'hover:ring-2 hover:ring-indigo-400'
              }`}
            >
              {imageBlobs[image.id] && (
                <Image
                  src={imageBlobs[image.id]}
                  alt={`Thumbnail ${index + 1}`}
                  className="w-full h-full object-cover rounded-md"
                  width={96}
                  height={54}
                  unoptimized
                />
              )}
              <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 transition-opacity" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
} 