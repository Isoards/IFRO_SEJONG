// Google Maps API 동적 로더
export interface GoogleMapsLoaderOptions {
  apiKey: string;
  language?: string;
  region?: string;
  libraries?: string[];
}

class GoogleMapsLoader {
  private static instance: GoogleMapsLoader;
  private loadPromise: Promise<void> | null = null;
  private currentLanguage: string | null = null;

  private constructor() {}

  public static getInstance(): GoogleMapsLoader {
    if (!GoogleMapsLoader.instance) {
      GoogleMapsLoader.instance = new GoogleMapsLoader();
    }
    return GoogleMapsLoader.instance;
  }

  public async load(options: GoogleMapsLoaderOptions): Promise<void> {
    const { apiKey, language = 'ko', region = 'KR', libraries = [] } = options;

    // 이미 같은 언어로 로드되어 있으면 기존 Promise 반환
    if (this.currentLanguage === language && this.loadPromise) {
      return this.loadPromise;
    }

    // 기존 스크립트가 있으면 제거 (언어 변경 시)
    if (this.currentLanguage && this.currentLanguage !== language) {
      this.removeExistingScript();
    }

    // 새로운 언어로 로드
    this.currentLanguage = language;
    this.loadPromise = this.loadScript(apiKey, language, region, libraries);
    
    return this.loadPromise;
  }

  private removeExistingScript(): void {
    // 기존 Google Maps 스크립트 제거
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
    if (existingScript) {
      existingScript.remove();
    }

    // Google Maps 관련 전역 객체 정리
    if (window.google) {
      delete (window as any).google;
    }
  }

  private loadScript(
    apiKey: string, 
    language: string, 
    region?: string, 
    libraries: string[] = []
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      // 이미 로드되어 있는지 확인
      if (window.google && window.google.maps) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.type = 'text/javascript';
      
      // URL 파라미터 구성
      const params = new URLSearchParams({
        key: apiKey,
        language: language,
        callback: 'initGoogleMaps'
      });

      if (region) {
        params.append('region', region);
      }

      if (libraries.length > 0) {
        params.append('libraries', libraries.join(','));
      }

      script.src = `https://maps.googleapis.com/maps/api/js?${params.toString()}`;

      // 콜백 함수 설정
      (window as any).initGoogleMaps = () => {
        delete (window as any).initGoogleMaps;
        resolve();
      };

      script.onerror = () => {
        delete (window as any).initGoogleMaps;
        reject(new Error('Google Maps API 로드 실패'));
      };

      document.head.appendChild(script);
    });
  }

  public isLoaded(): boolean {
    return !!(window.google && window.google.maps);
  }

  public getCurrentLanguage(): string | null {
    return this.currentLanguage;
  }
}

export default GoogleMapsLoader;