const API = process.env.REACT_APP_BACKEND_URL;

const DEFAULT_AVATARS = {
  male: '/avatars/male.png',
  female: '/avatars/female.png',
  prefer_not_to_say: '/avatars/neutral.png',
  neutral: '/avatars/neutral.png',
};

export function getAvatarUrl(member) {
  if (!member) return DEFAULT_AVATARS.neutral;
  
  // Custom uploaded avatar
  if (member.avatar_path) {
    return `${API}/api/files/${member.avatar_path}`;
  }
  if (member.avatar_url && member.avatar_url.startsWith('http')) {
    return member.avatar_url;
  }
  
  // Default by gender
  const gender = member.gender || 'prefer_not_to_say';
  return DEFAULT_AVATARS[gender] || DEFAULT_AVATARS.neutral;
}

export function MemberAvatar({ member, size = 40, className = '' }) {
  const url = getAvatarUrl(member);
  return (
    <img
      src={url}
      alt={member?.name || 'Avatar'}
      className={`rounded-full object-cover bg-zinc-800 ${className}`}
      style={{ width: size, height: size, minWidth: size }}
      onError={(e) => { e.target.src = DEFAULT_AVATARS.neutral; }}
    />
  );
}
