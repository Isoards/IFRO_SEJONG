import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Minimize2 } from "lucide-react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
}

interface ChatBotPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatBotPanel: React.FC<ChatBotPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "안녕하세요! IFRO 교통 분석 AI 어시스턴트입니다. 교통 데이터나 대시보드 사용법에 대해 궁금한 점이 있으시면 언제든 물어보세요!",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 메시지 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 패널이 열릴 때 입력창에 포커스
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      // TODO: 실제 AI API 호출 구현
      // 현재는 더미 응답
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateDummyResponse(userMessage.content),
        sender: "bot",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("AI 응답 생성 중 오류:", error);
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content:
          "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 더미 응답 생성 함수 (실제 AI API로 대체 예정)
  const generateDummyResponse = (userInput: string): string => {
    const lowerInput = userInput.toLowerCase();

    if (lowerInput.includes("교통량") || lowerInput.includes("통행량")) {
      return "교통량 데이터는 대시보드의 '분석' 탭에서 확인하실 수 있습니다. 특정 교차로를 클릭하시면 해당 지점의 상세한 교통량 정보를 볼 수 있어요.";
    } else if (lowerInput.includes("사고") || lowerInput.includes("incident")) {
      return "교통사고 정보는 '사고' 탭에서 확인 가능합니다. 빨간색 삼각형 아이콘을 클릭하시면 사고 목록과 상세 정보를 볼 수 있습니다.";
    } else if (lowerInput.includes("경로") || lowerInput.includes("route")) {
      return "경로 분석은 '교통흐름' 탭에서 이용하실 수 있습니다. 지도에서 두 지점을 선택하시면 해당 구간의 교통 흐름을 분석해드립니다.";
    } else if (
      lowerInput.includes("즐겨찾기") ||
      lowerInput.includes("favorite")
    ) {
      return "관심 있는 교차로나 사고를 즐겨찾기에 추가하실 수 있습니다. 별표 아이콘을 클릭하시면 '즐겨찾기' 탭에서 쉽게 찾아보실 수 있어요.";
    } else if (
      lowerInput.includes("help") ||
      lowerInput.includes("도움") ||
      lowerInput.includes("사용법")
    ) {
      return "IFRO 대시보드 사용법:\n\n🚗 분석: 교차로별 교통량 분석\n🔄 교통흐름: 두 지점 간 경로 분석\n⚠️ 사고: 교통사고 현황\n⭐ 즐겨찾기: 관심 지점 관리\n📊 Tableau: 고급 분석 대시보드\n\n더 자세한 정보가 필요하시면 구체적으로 물어보세요!";
    } else {
      return "네, 무엇을 도와드릴까요? 교통 데이터 분석, 대시보드 사용법, 특정 기능에 대해 궁금한 점이 있으시면 언제든 말씀해 주세요!";
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className={`
      fixed bottom-48 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl
      border border-gray-200 z-[999] flex flex-col
      transform transition-all duration-300 ease-in-out
      md:bottom-44 md:right-8 md:w-96
      max-w-[calc(100vw-3rem)] max-h-[calc(100vh-10rem)]
      ${isOpen ? "scale-100 opacity-100" : "scale-95 opacity-0"}
    `}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-blue-50 rounded-t-lg">
        <div className="flex items-center space-x-2">
          <Bot className="w-6 h-6 text-blue-600" />
          <h3 className="font-semibold text-gray-800">AI 어시스턴트</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded transition-colors"
          title="채팅 최소화"
        >
          <Minimize2 size={18} className="text-gray-600" />
        </button>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`flex items-start space-x-2 max-w-[80%] ${
                message.sender === "user"
                  ? "flex-row-reverse space-x-reverse"
                  : ""
              }`}
            >
              <div
                className={`
                w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${message.sender === "user" ? "bg-blue-500" : "bg-gray-300"}
              `}
              >
                {message.sender === "user" ? (
                  <User size={16} className="text-white" />
                ) : (
                  <Bot size={16} className="text-gray-600" />
                )}
              </div>
              <div
                className={`
                p-3 rounded-lg whitespace-pre-wrap
                ${
                  message.sender === "user"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-gray-100 text-gray-800 rounded-bl-none"
                }
              `}
              >
                {message.content}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                <Bot size={16} className="text-gray-600" />
              </div>
              <div className="bg-gray-100 p-3 rounded-lg rounded-bl-none">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="메시지를 입력하세요..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`
              px-4 py-2 rounded-lg transition-colors
              ${
                inputMessage.trim() && !isLoading
                  ? "bg-blue-500 hover:bg-blue-600 text-white"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }
            `}
          >
            <Send size={18} />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Enter를 눌러 전송, Shift+Enter로 줄바꿈
        </p>
      </div>
    </div>
  );
};
