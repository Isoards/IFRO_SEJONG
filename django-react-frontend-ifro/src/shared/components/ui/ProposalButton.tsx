import React from "react";
import { useNavigate } from "react-router-dom";
import { FileText } from "lucide-react";

const ProposalButton: React.FC = () => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate("/proposals")}
      className="fixed bottom-4 left-4 w-14 h-14 bg-green-600 hover:bg-green-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 z-50 flex items-center justify-center group"
      title="정책제안 보기"
    >
      <FileText size={24} />

      {/* 툴팁 */}
      <div className="absolute left-16 bottom-1/2 transform translate-y-1/2 bg-gray-800 text-white px-3 py-2 rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        정책제안
        <div className="absolute left-0 top-1/2 transform -translate-x-1 -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-gray-800"></div>
      </div>
    </button>
  );
};

export default ProposalButton;
