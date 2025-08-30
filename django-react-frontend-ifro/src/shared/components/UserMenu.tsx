import { useNavigate } from "react-router-dom";
import { User, LogOut, FileSliders } from "lucide-react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

export default function UserMenu() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/login");
  };

  const handleSettings = () => {
    navigate("/settings");
  };

  const handleAdmin = () => {
    navigate("/admin");
  };

  return (
    <div className="w-full flex flex-col items-center">
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button className="p-2 rounded-full hover:bg-gray-200 transition bg-white shadow">
            <User size={24} />
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            side="top"
            align="center"
            className="bg-white rounded shadow-lg py-2 px-4 z-50"
          >
            <DropdownMenu.Item
              onClick={handleAdmin}
              className="cursor-pointer flex items-center gap-2 text-gray-700 hover:bg-gray-100 px-2 py-1 rounded outline-none"
            >
              <FileSliders size={16} /> AdminDashboard
            </DropdownMenu.Item>
            <DropdownMenu.Item
              onClick={handleSettings}
              className="cursor-pointer flex items-center gap-2 text-gray-700 hover:bg-gray-100 px-2 py-1 rounded outline-none"
            >
              <User size={16} /> Settings
            </DropdownMenu.Item>
            <DropdownMenu.Separator className="my-1 h-px bg-gray-200" />
            <DropdownMenu.Item
              onClick={handleLogout}
              className="cursor-pointer flex items-center gap-2 text-red-600 hover:bg-gray-100 px-2 py-1 rounded outline-none"
            >
              <LogOut size={16} /> Logout
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </div>
  );
}
