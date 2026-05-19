export function validatePassword(p: string): string | null {
    if (p.length < 8) return 'Password must be at least 8 characters long';
    if (!/[A-Z]/.test(p)) return 'Password must contain an uppercase letter';
    if (!/\d/.test(p)) return 'Password must contain a digit';
    if (!/[!@#$%^&*]/.test(p)) return 'Password must contain a special character';
    return null;
}
