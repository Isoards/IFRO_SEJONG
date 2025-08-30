import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { User } from "lucide-react";
import {
  getCurrentUser,
  updateUserInfo,
  changePassword,
  deleteAccount,
} from "../services/user";
import LanguageSelector from "./ui/LanguageSelector";

const ENCRYPTION_METHODS = ["AES", "RSA", "SHA256"];

export default function Settings() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [editMode, setEditMode] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [encryptionEnabled, setEncryptionEnabled] = useState(false);
  const [encryptionMethod, setEncryptionMethod] = useState(
    ENCRYPTION_METHODS[0]
  );
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  useEffect(() => {
    // Load encryption setting from localStorage
    const savedEncryption = localStorage.getItem("encryptionEnabled");
    if (savedEncryption) {
      setEncryptionEnabled(JSON.parse(savedEncryption));
    }

    (async () => {
      const u = await getCurrentUser();
      setUser(u);
      setEditName(u?.name || "");
      setEditEmail(u?.email || "");
      setSelectedLanguage(i18n.language || "en"); // 현재 언어 설정
    })();
  }, [i18n.language]); // i18n.language를 의존성 배열에 추가

  // 프로필 정보 저장
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const updated = await updateUserInfo({
        name: editName,
        email: editEmail,
      });
      setUser(updated);
      setEditMode(false);
      alert(t("profile.userInfoUpdated"));
    } catch {
      alert(t("profile.failedToUpdate"));
    }
  };

  // 비밀번호 변경
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert(t("profile.passwordsDoNotMatch"));
      return;
    }
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      alert(t("profile.passwordChanged"));
      setShowPasswordModal(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      alert(
        err?.response?.data?.detail ||
          err?.response?.data ||
          t("profile.failedToChangePassword")
      );
    }
  };

  // 암호화 설정 저장
  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    // 선택된 언어 적용
    if (selectedLanguage !== i18n.language) {
      i18n.changeLanguage(selectedLanguage);
    }
    // 암호화 설정 저장 로직 필요시 추가
    localStorage.setItem(
      "encryptionEnabled",
      JSON.stringify(encryptionEnabled)
    );
    // 설정 저장 메시지 표시 (자동으로 사라지지 않음)
    setShowSuccessMessage(true);
  };

  // 언어 변경 핸들러 (임시 저장)
  const handleLanguageChange = (languageCode: string) => {
    setSelectedLanguage(languageCode);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 py-8">
      {/* 프로필 카드 */}
      <div className="w-full max-w-lg rounded-2xl shadow-xl border bg-white p-8 mb-6">
        <div className="flex items-center gap-4 mb-6">
          <User size={48} className="text-blue-500" />
          <h2 className="text-2xl font-bold">{t("profile.title")}</h2>
        </div>
        {!editMode ? (
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600 font-medium">
                {t("profile.name")}
              </span>
              <span className="font-semibold text-gray-800">
                {user?.name || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600 font-medium">
                {t("profile.username")}
              </span>
              <span className="font-semibold text-gray-800">
                {user?.username || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600 font-medium">
                {t("profile.email")}
              </span>
              <span className="font-semibold text-gray-800">
                {user?.email || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 font-medium">
                {t("profile.role")}
              </span>
              <span className="font-semibold text-gray-800">
                {user?.role || "-"}
              </span>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                className="flex-1 bg-blue-100 text-blue-700 py-2 px-4 rounded-md hover:bg-blue-200 transition-colors"
                onClick={() => setEditMode(true)}
              >
                {t("common.edit")}
              </button>
              <button
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors"
                onClick={() => setShowPasswordModal(true)}
              >
                {t("profile.changePassword")}
              </button>
              <button
                className="flex-1 bg-red-100 text-red-700 py-2 px-4 rounded-md hover:bg-red-200 transition-colors"
                onClick={() => setShowDeleteModal(true)}
              >
                {t("profile.deleteAccount")}
              </button>
            </div>
          </div>
        ) : (
          <form className="space-y-4" onSubmit={handleSaveProfile}>
            <div>
              <label className="block text-gray-600 font-medium mb-1">
                {t("profile.name")}
              </label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-gray-600 font-medium mb-1">
                {t("profile.email")}
              </label>
              <input
                type="email"
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="flex-1 bg-blue-100 text-blue-700 py-2 px-4 rounded-md hover:bg-blue-200 transition-colors"
              >
                {t("common.save")}
              </button>
              <button
                type="button"
                className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
                onClick={() => setEditMode(false)}
              >
                {t("common.cancel")}
              </button>
            </div>
          </form>
        )}
      </div>
      {/* 설정 카드 */}
      <div className="w-full max-w-lg rounded-2xl shadow-xl border bg-white p-8 mb-6">
        <h3 className="text-xl font-semibold mb-4">
          {t("navigation.settings")}
        </h3>

        {/* 성공 메시지 */}
        {showSuccessMessage && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-md flex items-center justify-between">
            <span>{t("profile.settingsSaved")}</span>
            <button
              type="button"
              onClick={() => setShowSuccessMessage(false)}
              className="ml-2 text-green-600 hover:text-green-800 font-bold text-lg leading-none"
            >
              ×
            </button>
          </div>
        )}

        <form className="space-y-6" onSubmit={handleSaveSettings}>
          <div>
            <LanguageSelector
              showLabel={true}
              autoSave={false}
              onLanguageChange={handleLanguageChange}
              selectedLanguage={selectedLanguage}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">
              {t("profile.encryptionEnabled")}
            </span>
            <button
              type="button"
              onClick={() => setEncryptionEnabled((v) => !v)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                encryptionEnabled
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              {encryptionEnabled ? t("profile.on") : t("profile.off")}
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">
              {t("profile.encryptionMethod")}
            </span>
            <select
              value={encryptionMethod}
              onChange={(e) => setEncryptionMethod(e.target.value)}
              disabled={!encryptionEnabled}
              className="w-32 px-3 py-2 border border-gray-300 rounded-md text-sm disabled:bg-gray-100 disabled:text-gray-500"
            >
              {ENCRYPTION_METHODS.map((method) => (
                <option key={method} value={method}>
                  {method}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="w-full mt-2 bg-blue-100 text-blue-700 py-2 px-4 rounded-md hover:bg-blue-200 transition-colors"
          >
            {t("common.save")}
          </button>
        </form>
      </div>
      {/* 비밀번호 변경 모달 */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-blue-600 mb-4">
              {t("profile.changePassword")}
            </h3>
            <form className="space-y-4" onSubmit={handleChangePassword}>
              <div>
                <label className="block text-gray-600 font-medium mb-1">
                  {t("profile.currentPassword")}
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-gray-600 font-medium mb-1">
                  {t("profile.newPassword")}
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-gray-600 font-medium mb-1">
                  {t("profile.confirmPassword")}
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-100 text-blue-700 py-2 px-4 rounded-md hover:bg-blue-200 transition-colors"
                >
                  {t("common.save")}
                </button>
                <button
                  type="button"
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
                  onClick={() => setShowPasswordModal(false)}
                >
                  {t("common.cancel")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* 계정 삭제 모달 */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-red-600 mb-4">
              {t("profile.deleteAccountConfirm")}
            </h3>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={async () => {
                  try {
                    await deleteAccount();
                    localStorage.removeItem("access");
                    localStorage.removeItem("refresh");
                    alert(t("profile.accountDeleted"));
                    navigate("/login");
                  } catch (err: any) {
                    alert(
                      err?.response?.data?.detail ||
                        err?.response?.data ||
                        t("profile.failedToDeleteAccount")
                    );
                  }
                  setShowDeleteModal(false);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                {t("common.delete")}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 대시보드로 돌아가기 버튼 */}
      <div className="w-full max-w-lg mt-4">
        <button
          type="button"
          className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors"
          onClick={() => navigate("/dashboard")}
        >
          {t("dashboard.backToDashboard")}
        </button>
      </div>
    </div>
  );
}
