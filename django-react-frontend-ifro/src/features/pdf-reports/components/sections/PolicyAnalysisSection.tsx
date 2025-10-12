import React from 'react';
import { useTranslation } from 'react-i18next';
import { PolicyEvaluation, AIPolicyProposal } from '../../../../shared/types/global.types';

interface PolicyAnalysisSectionProps {
  policyEvaluation?: PolicyEvaluation;
  policyProposals?: AIPolicyProposal[];
  citizenConcerns?: string[];
  dataDrivenInsights?: string[];
  className?: string;
}

export const PolicyAnalysisSection: React.FC<PolicyAnalysisSectionProps> = ({
  policyEvaluation,
  policyProposals = [],
  citizenConcerns = [],
  dataDrivenInsights = [],
  className = "",
}) => {
  const { t } = useTranslation();

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
      case 'urgent':
        return 'text-red-600 bg-red-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'text-blue-600 bg-blue-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'hard':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getCostColor = (cost: string) => {
    switch (cost) {
      case 'low':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'high':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className={`policy-analysis-section ${className}`}>
      {/* 정책 평가 섹션 */}
      {policyEvaluation && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            📊 정책 평가
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 안전 우선순위 */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-2">안전 우선순위</h4>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(policyEvaluation.safety_priority)}`}>
                {policyEvaluation.safety_priority === 'high' ? '높음' : 
                 policyEvaluation.safety_priority === 'medium' ? '보통' : '낮음'}
              </span>
            </div>

            {/* 신호 최적화 */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-2">신호 최적화</h4>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(policyEvaluation.signal_optimization)}`}>
                {policyEvaluation.signal_optimization === 'urgent' ? '긴급' :
                 policyEvaluation.signal_optimization === 'needed' ? '필요' : '불필요'}
              </span>
            </div>
          </div>

          {/* 인프라 필요사항 */}
          {policyEvaluation.infrastructure_needs.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-gray-700 mb-2">인프라 개선 필요사항</h4>
              <ul className="list-disc list-inside space-y-1">
                {policyEvaluation.infrastructure_needs.map((need: string, index: number) => (
                  <li key={index} className="text-gray-600">{need}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 접근성 문제 */}
          {policyEvaluation.accessibility_issues.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-gray-700 mb-2">접근성 문제</h4>
              <ul className="list-disc list-inside space-y-1">
                {policyEvaluation.accessibility_issues.map((issue: string, index: number) => (
                  <li key={index} className="text-gray-600">{issue}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 정책 제안 섹션 */}
      {policyProposals.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            💡 정책 제안
          </h3>
          
          <div className="space-y-4">
            {policyProposals.map((proposal, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-gray-800">{proposal.title}</h4>
                  <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {proposal.category === 'traffic_signal' ? '신호등' :
                     proposal.category === 'road_safety' ? '도로안전' :
                     proposal.category === 'traffic_flow' ? '교통흐름' :
                     proposal.category === 'infrastructure' ? '인프라' :
                     proposal.category === 'policy' ? '정책' : '기타'}
                  </span>
                </div>
                
                <p className="text-gray-600 mb-3">{proposal.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  <div className="flex flex-col">
                    <span className="text-gray-500">우선순위</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(proposal.priority)}`}>
                      {proposal.priority === 'urgent' ? '긴급' :
                       proposal.priority === 'high' ? '높음' :
                       proposal.priority === 'medium' ? '보통' : '낮음'}
                    </span>
                  </div>
                  
                  <div className="flex flex-col">
                    <span className="text-gray-500">예상 효과</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColor(proposal.expected_impact)}`}>
                      {proposal.expected_impact === 'high' ? '높음' :
                       proposal.expected_impact === 'medium' ? '보통' : '낮음'}
                    </span>
                  </div>
                  
                  <div className="flex flex-col">
                    <span className="text-gray-500">실행 난이도</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getDifficultyColor(proposal.implementation_difficulty)}`}>
                      {proposal.implementation_difficulty === 'easy' ? '쉬움' :
                       proposal.implementation_difficulty === 'medium' ? '보통' : '어려움'}
                    </span>
                  </div>
                  
                  <div className="flex flex-col">
                    <span className="text-gray-500">예상 비용</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getCostColor(proposal.estimated_cost)}`}>
                      {proposal.estimated_cost === 'low' ? '낮음' :
                       proposal.estimated_cost === 'medium' ? '보통' : '높음'}
                    </span>
                  </div>
                </div>
                
                <div className="mt-2 text-sm text-gray-500">
                  예상 기간: {proposal.timeline === 'short' ? '단기' :
                           proposal.timeline === 'medium' ? '중기' : '장기'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 시민 우려사항 섹션 */}
      {citizenConcerns.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            👥 시민 우려사항
          </h3>
          <ul className="list-disc list-inside space-y-2">
            {citizenConcerns.map((concern, index) => (
              <li key={index} className="text-gray-600">{concern}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 데이터 기반 인사이트 섹션 */}
      {dataDrivenInsights.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            📈 데이터 기반 인사이트
          </h3>
          <ul className="list-disc list-inside space-y-2">
            {dataDrivenInsights.map((insight, index) => (
              <li key={index} className="text-gray-600">{insight}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
