import { useCallback, useState } from 'react';
import html2canvas from 'html2canvas';

interface UseChartImageOptions {
  backgroundColor?: string;
  scale?: number;
  quality?: number;
}

interface UseChartImageReturn {
  generateImage: (element: HTMLElement) => Promise<string>;
  isGenerating: boolean;
  error: string | null;
}

export const useChartImage = (options: UseChartImageOptions = {}): UseChartImageReturn => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    backgroundColor = '#ffffff',
    scale = 2,
    quality = 0.95
  } = options;

  const generateImage = useCallback(async (element: HTMLElement): Promise<string> => {
    if (!element) {
      setError('No element provided for image generation');
      return '';
    }

    setIsGenerating(true);
    setError(null);

    try {
      const canvas = await html2canvas(element, {
        backgroundColor,
        scale,
        logging: false,
        useCORS: true,
        allowTaint: true,
        removeContainer: true,
        imageTimeout: 15000,
        onclone: (clonedDoc) => {
          // Ensure all styles are properly applied to the cloned document
          const clonedElement = clonedDoc.querySelector('[data-chart-container]');
          if (clonedElement) {
            (clonedElement as HTMLElement).style.backgroundColor = backgroundColor;
          }
        }
      });

      const imageData = canvas.toDataURL('image/png', quality);
      setIsGenerating(false);
      return imageData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to generate chart image: ${errorMessage}`);
      setIsGenerating(false);
      console.error('Chart image generation error:', err);
      return '';
    }
  }, [backgroundColor, scale, quality]);

  return {
    generateImage,
    isGenerating,
    error
  };
};