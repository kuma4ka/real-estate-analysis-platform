import { useRef, useCallback, useEffect } from 'react';

/**
 * Returns a throttled version of an async function.
 * Uses refs (not state) for tracking, so the throttle window is
 * never accidentally reset by a re-render cycle.
 *
 * After the function resolves/rejects, it cannot fire again until
 * `delay` ms have elapsed since the call *completed*.
 */
function useThrottle<Args extends unknown[]>(
    fn: (...args: Args) => Promise<void>,
    delay: number
): (...args: Args) => void {
    const lastCompletedAt = useRef<number>(0);
    const isRunning = useRef<boolean>(false);
    // Keep fnRef in sync with the latest fn on every render.
    // useEffect (not useLayoutEffect) is correct here — updating a ref
    // does not require DOM access and does not need to run before paint.
    const fnRef = useRef(fn);
    useEffect(() => {
        fnRef.current = fn;
    });

    return useCallback(
        (...args: Args) => {
            const now = Date.now();
            if (isRunning.current) return;
            if (now - lastCompletedAt.current < delay) return;

            isRunning.current = true;
            fnRef.current(...args).finally(() => {
                lastCompletedAt.current = Date.now();
                isRunning.current = false;
            });
        },
        [delay] // only `delay` matters — fnRef is always current
    );
}

export default useThrottle;
