import api from "./axios";

export async function getCurrentUser() {
  // access 토큰이 있으면 user 정보를 반환하는 엔드포인트가 필요함
  // 실제로는 백엔드에 /user/me 같은 엔드포인트가 필요하지만, 현재는 /auth/login에서 반환하는 구조를 참고
  // 여기서는 access 토큰만으로는 user 정보를 얻을 수 없으므로, 추후 /user/me 엔드포인트가 필요함
  // 임시로 access 토큰의 payload를 decode해서 사용하거나, 추후 API 연동 필요
  // 아래는 예시 코드
  const token = localStorage.getItem("access");
  if (!token) return null;

  // JWT payload decode (base64)
  function parseJwt(token: string) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch {
      return null;
    }
  }

  const payload = parseJwt(token);
  if (!payload) return null;

  // payload에 username, user_id, email, role 등이 들어있다고 가정
  return {
    id: payload.user_id || payload.id,
    username: payload.username,
    email: payload.email,
    name: payload.name,
    role: payload.role,
  };
}

export async function updateUserInfo({ name, email }: { name: string; email: string }) {
  const res = await api.patch("auth/user/me", { name, email });
  return res.data;
}

export async function changePassword({ current_password, new_password }: { current_password: string; new_password: string }) {
  const res = await api.patch("auth/user/me/password", { current_password, new_password });
  return res.data;
}

export async function deleteAccount() {
  const res = await api.delete("auth/user/me");
  return res.data;
} 