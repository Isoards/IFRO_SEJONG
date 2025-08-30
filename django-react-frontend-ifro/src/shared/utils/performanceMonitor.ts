// Performance monitoring utilities
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, number> = new Map();

  private constructor() {}

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  public startTimer(label: string): void {
    this.metrics.set(label, performance.now());
  }

  public endTimer(label: string): number {
    const startTime = this.metrics.get(label);
    if (!startTime) {
      console.warn(`Timer '${label}' was not started`);
      return 0;
    }
    
    const duration = performance.now() - startTime;
    this.metrics.delete(label);
    
    if (process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true') {
      console.log(`⏱️ ${label}: ${duration.toFixed(2)}ms`);
    }
    
    return duration;
  }

  public measureAsync<T>(label: string, asyncFn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.startTimer(label);
      asyncFn()
        .then((result) => {
          this.endTimer(label);
          resolve(result);
        })
        .catch((error) => {
          this.endTimer(label);
          reject(error);
        });
    });
  }

  public reportWebVitals(): void {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true') {
            console.log(`📊 ${entry.name}: ${entry.duration?.toFixed(2) || 'N/A'}ms`);
          }
        });
      });

      observer.observe({ entryTypes: ['measure', 'navigation'] });
    }
  }
}

export const performanceMonitor = PerformanceMonitor.getInstance();
