import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Home,
  FileText,
  Settings,
  LogOut,
  User,
  BarChart3,
} from "lucide-react";
import { getCurrentUser } from "../../services/user";

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = React.useState<any>(null);

  React.useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
      } catch (error) {
        console.error("사용자 정보 로딩 실패:", error);
      }
    };
    loadUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/login");
  };

  const isActive = (path: string) => {
    if (path === "/dashboard") {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  const navItems = [
    { path: "/dashboard", icon: Home, label: "대시보드" },
    { path: "/proposals", icon: FileText, label: "정책제안" },
    { path: "/settings", icon: Settings, label: "설정" },
  ];

  // 관리자용 메뉴
  if (currentUser?.role === "admin") {
    navItems.splice(2, 0, {
      path: "/admin/proposals",
      icon: BarChart3,
      label: "정책제안 관리",
    });
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* 사이드바 */}
      <aside className="w-64 bg-white shadow-sm border-r border-gray-200 flex flex-col relative">
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">IFRO</span>
            </div>
            <h1 className="text-xl font-bold text-gray-800">교통 시스템</h1>
          </div>
        </div>

        <nav className="px-4 space-y-1 flex-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <Icon size={20} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* 사용자 정보 */}
        <div className="p-4 border-t border-gray-200 w-64">
          {currentUser ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <User size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {currentUser.name || currentUser.username}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {currentUser.email}
                  </p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut size={16} />
                로그아웃
              </button>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm text-gray-500">로딩 중...</p>
            </div>
          )}
        </div>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
};

export default MainLayout;
