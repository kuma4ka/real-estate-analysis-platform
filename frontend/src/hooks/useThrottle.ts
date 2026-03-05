import { useRef, useCallback } from 'react';

/**
 * Returns a throttled version of the given async function.
 * After the function completes (resolves or rejects), it cannot be called again
 * for `delay` milliseconds.
 */
function useThrottle<T extends (...args: unknown[]) => Promise<void>>(
    fn: T,
    delay: number
): T {
    const lastCalledAt = useRef<number>(0);
    const isRunning = useRef<boolean>(false);

    const throttled = useCallback(
        async (...args: unknown[]) => {
            const now = Date.now();
            if (isRunning.current) return;
            if (now - lastCalledAt.current < delay) return;

            isRunning.current = true;
            try {
                await fn(...args as Parameters<T>);
            } finally {
                lastCalledAt.current = Date.now();
                isRunning.current = false;
            }
        },
        [fn, delay]
    );

    return throttled as T;
}

export default useThrottle;
