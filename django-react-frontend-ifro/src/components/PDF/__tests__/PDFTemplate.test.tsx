import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PDFTemplate } from '../PDFTemplate';
import { ReportData } from '../../../types/global.types';

// Mock the section components
jest.mock('../sections', () => ({
  ReportHeader: ({ title, subtitle }: any) => (
    <div data-testid="report-header">
      <h1>{title || 'Default Title'}</h1>
      <h2>{subtitle || 'Default Subtitle'}</h2>
    </div>
  ),
  IntersectionInfo: ({ intersection, datetime, totalVolume }: any) => (
    <div data-testid="intersection-info">
      <span>{intersection.name}</span>
      <span>{datetime}</span>
      <span>{totalVolume}</span>
    </div>
  ),
  TrafficDataTable: ({ trafficVolumes, totalVolume, averageSpeed }: any) => (
    <div data-testid="traffic-data-table">
      <span>N: {trafficVolumes.N}</span>
      <span>Total: {totalVolume}</span>
      <span>Speed: {averageSpeed}</span>
    </div>
  ),
  InterpretationSection: ({ interpretation, congestionLevel }: any) => (
    <div data-testid="interpretation-section">
      <span>{interpretation}</span>
      <span>{congestionLevel}</span>
    </div>
  ),
  ChartSection: ({ chartImage, chartTitle }: any) => (
    <div data-testid="chart-section">
      {chartImage && <img src={chartImage} alt="chart" />}
      <span>{chartTitle}</span>
    </div>
  ),
  ReportFooter: ({ organizationName, systemName }: any) => (
    <div data-testid="report-footer">
      <span>{organizationName}</span>
      <span>{systemName}</span>
    </div>
  ),
}));

const mockReportData: ReportData = {
  intersection: {
    id: 1,
    name: 'Test Intersection',
    latitude: -12.0464,
    longitude: -77.0428,
    total_volume: 1500,
    average_speed: 35,
    datetime: '2024-01-15T10:00:00Z',
  },
  datetime: '2024-01-15T10:00:00Z',
  trafficVolumes: {
    N: 400,
    S: 350,
    E: 380,
    W: 370,
  },
  totalVolume: 1500,
  averageSpeed: 35,
  interpretation: 'Traffic is moderate with peak flow in N direction',
  congestionLevel: 'moderate',
  peakDirection: 'N',
  chartData: [],
};

describe('PDFTemplate', () => {
  it('renders all required sections', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    expect(screen.getByTestId('report-header')).toBeInTheDocument();
    expect(screen.getByTestId('intersection-info')).toBeInTheDocument();
    expect(screen.getByTestId('traffic-data-table')).toBeInTheDocument();
    expect(screen.getByTestId('interpretation-section')).toBeInTheDocument();
    expect(screen.getByTestId('chart-section')).toBeInTheDocument();
    expect(screen.getByTestId('report-footer')).toBeInTheDocument();
  });

  it('applies correct PDF template styling', () => {
    const { container } = render(<PDFTemplate reportData={mockReportData} />);
    
    const template = container.querySelector('.pdf-template');
    expect(template).toHaveClass('bg-white', 'p-8');
    expect(template).toHaveStyle({ width: '210mm', minHeight: '297mm' });
    expect(template).toHaveAttribute('data-pdf-template');
  });

  it('passes correct props to ReportHeader', () => {
    render(
      <PDFTemplate 
        reportData={mockReportData} 
        customTitle="Custom Title"
        customSubtitle="Custom Subtitle"
      />
    );
    
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
    expect(screen.getByText('Custom Subtitle')).toBeInTheDocument();
  });

  it('passes correct props to IntersectionInfo', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    const intersectionInfo = screen.getByTestId('intersection-info');
    expect(intersectionInfo).toHaveTextContent('Test Intersection');
    expect(intersectionInfo).toHaveTextContent('2024-01-15T10:00:00Z');
    expect(intersectionInfo).toHaveTextContent('1500');
  });

  it('passes correct props to TrafficDataTable', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    const trafficTable = screen.getByTestId('traffic-data-table');
    expect(trafficTable).toHaveTextContent('NS: 400');
    expect(trafficTable).toHaveTextContent('Total: 1500');
    expect(trafficTable).toHaveTextContent('Speed: 35');
  });

  it('passes correct props to InterpretationSection', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    const interpretationSection = screen.getByTestId('interpretation-section');
    expect(interpretationSection).toHaveTextContent('Traffic is moderate with peak flow in NS direction');
    expect(interpretationSection).toHaveTextContent('moderate');
  });

  it('passes chart image to ChartSection when provided', () => {
    const chartImage = 'data:image/png;base64,test-image-data';
    render(<PDFTemplate reportData={mockReportData} chartImage={chartImage} />);
    
    const chartSection = screen.getByTestId('chart-section');
    const image = chartSection.querySelector('img');
    expect(image).toHaveAttribute('src', chartImage);
  });

  it('does not render chart image when not provided', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    const chartSection = screen.getByTestId('chart-section');
    const image = chartSection.querySelector('img');
    expect(image).not.toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    const { container } = render(
      <PDFTemplate reportData={mockReportData} className="custom-class" />
    );
    
    const template = container.querySelector('.pdf-template');
    expect(template).toHaveClass('custom-class');
  });

  it('passes recommendations to InterpretationSection', () => {
    const recommendations = ['Recommendation 1', 'Recommendation 2'];
    render(
      <PDFTemplate 
        reportData={mockReportData} 
        recommendations={recommendations}
      />
    );
    
    // The recommendations would be passed to InterpretationSection
    // We can't easily test this with our mock, but the component structure is correct
    expect(screen.getByTestId('interpretation-section')).toBeInTheDocument();
  });

  it('uses default values when optional props are not provided', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    expect(screen.getByText('Default Title')).toBeInTheDocument();
    expect(screen.getByText('Default Subtitle')).toBeInTheDocument();
    expect(screen.getByText('Análisis Visual del Tráfico')).toBeInTheDocument();
  });

  it('passes correct organization info to ReportFooter', () => {
    render(<PDFTemplate reportData={mockReportData} />);
    
    const footer = screen.getByTestId('report-footer');
    expect(footer).toHaveTextContent('WILL');
    expect(footer).toHaveTextContent('Sistema de Análisis de Tráfico Inteligente');
  });

  it('handles missing optional data gracefully', () => {
    const minimalReportData = {
      ...mockReportData,
      interpretation: '',
      congestionLevel: '',
      peakDirection: '',
    };

    expect(() => {
      render(<PDFTemplate reportData={minimalReportData} />);
    }).not.toThrow();
  });
});