export const UserRole = {
  ADMIN: 'Admin',
  ANALYST: 'Analyst',
  USER: 'User',
  GUEST: 'Guest',
} as const;

export type UserRole = typeof UserRole[keyof typeof UserRole];
