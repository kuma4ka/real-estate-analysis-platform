import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    ComposedChart,
    Line,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';
import { fetchForecast, type ForecastData, type ForecastPoint } from '../services/api';
import type { StatsData } from '../services/api';

interface Props {
    /** Actual historical trend from the stats payload (used as the left axis anchor) */
    recentTrend: StatsData['recent_trend'];
}

const formatPrice = (v: number) => {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}k`;
    return `$${v}`;
};

// Quality description for the R² badge — labels are looked up via i18n
const rSquaredLabel = (r2: number, t: (key: string) => string): { label: string; color: string } => {
    if (r2 >= 0.8) return { label: t('analytics_forecast_fit_strong'), color: 'text-emerald-400' };
    if (r2 >= 0.5) return { label: t('analytics_forecast_fit_moderate'), color: 'text-yellow-400' };
    return { label: t('analytics_forecast_fit_weak'), color: 'text-red-400' };
};

const PriceForecastChart: React.FC<Props> = ({ recentTrend }) => {
    const { t } = useTranslation();
    const [forecast, setForecast] = useState<ForecastData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchForecast()
            .then(setForecast)
            .catch((err: unknown) =>
                setError(err instanceof Error ? err.message : 'Forecast unavailable')
            )
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="bg-surface rounded-xl border border-border p-5 shadow-card animate-pulse">
                <div className="h-4 bg-border rounded w-48 mb-4" />
                <div className="h-64 bg-border rounded" />
            </div>
        );
    }

    if (error || !forecast) {
        return (
            <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                <h3 className="text-sm font-semibold text-text-main mb-2">
                    {t('analytics_forecast_title', 'Price Forecast (30 days)')}
                </h3>
                <p className="text-sm text-text-muted">
                    {error ?? t('analytics_forecast_unavailable', 'Forecast data unavailable')}
                </p>
            </div>
        );
    }

    // ── Build unified dataset ──────────────────────────────────────────────
    // Historical points (actual price, no confidence band)
    type ChartPoint = {
        date: string;
        actual?: number;
        predicted?: number;
        band?: [number, number];   // [lower, upper] encoded as area range
        lower?: number;
        upper?: number;
        isForecast?: boolean;
    };

    const historical: ChartPoint[] = recentTrend.map(r => ({
        date: r.month,
        actual: r.avg_price,
    }));

    // Boundary point — last historical date gets both actual & predicted so the
    // two lines connect visually without a gap.
    const lastHist = historical[historical.length - 1];

    // First forecast point — bridge from last actual to first predicted
    const firstForecast = forecast.forecast[0];
    const bridgePoint: ChartPoint = {
        date: lastHist?.date ?? firstForecast.date,
        actual: lastHist?.actual,
        predicted: firstForecast.predicted_price,
        lower: firstForecast.lower,
        upper: firstForecast.upper,
        isForecast: false,
    };

    const forecastPoints: ChartPoint[] = forecast.forecast.map((p: ForecastPoint) => ({
        date: p.date,
        predicted: p.predicted_price,
        lower: p.lower,
        upper: p.upper,
        isForecast: true,
    }));

    const data: ChartPoint[] = [...historical, bridgePoint, ...forecastPoints];

    // Index of the last historical entry — used to draw the "today" reference line
    const todayIndex = historical.length - 1;
    const todayDate = historical[todayIndex]?.date;

    const { label: fitLabel, color: fitColor } = rSquaredLabel(forecast.r_squared, t);
    const trend = forecast.slope_per_day >= 0 ? '↑' : '↓';
    const trendColor = forecast.slope_per_day >= 0 ? 'text-emerald-400' : 'text-red-400';

    return (
        <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
            {/* Header */}
            <div className="flex items-start justify-between mb-4 flex-wrap gap-2">
                <div>
                    <h3 className="text-sm font-semibold text-text-main">
                        {t('analytics_forecast_title', 'Price Forecast — next 30 days')}
                    </h3>
                    <p className="text-xs text-text-muted mt-0.5">
                        {t('analytics_forecast_subtitle', 'Linear regression on historical daily avg prices')}
                    </p>
                </div>

                {/* Stats badges */}
                <div className="flex items-center gap-3 text-xs font-mono">
                    {/* R² badge */}
                    <div className="flex flex-col items-end">
                        <span className="text-text-muted">R²</span>
                        <span className={`font-bold ${fitColor}`}>
                            {forecast.r_squared.toFixed(3)}
                            <span className="ml-1 font-normal text-text-muted">({fitLabel})</span>
                        </span>
                    </div>
                    {/* Trend badge */}
                    <div className="flex flex-col items-end">
                        <span className="text-text-muted">{t('analytics_forecast_trend', 'Trend/day')}</span>
                        <span className={`font-bold ${trendColor}`}>
                            {trend} {formatPrice(Math.abs(forecast.slope_per_day))}
                        </span>
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 10 }}>
                    <defs>
                        <linearGradient id="forecastBand" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor="#5bc0c4" stopOpacity={0.18} />
                            <stop offset="95%" stopColor="#5bc0c4" stopOpacity={0.04} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--chart-grid)" />

                    <XAxis
                        dataKey="date"
                        tick={{ fill: 'var(--chart-text)', fontSize: 11 }}
                        tickFormatter={(val: string) => {
                            const d = new Date(val);
                            return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}`;
                        }}
                        minTickGap={30}
                    />
                    <YAxis
                        tickFormatter={formatPrice}
                        tick={{ fill: 'var(--chart-text)', fontSize: 11 }}
                        width={56}
                    />

                    <Tooltip
                        contentStyle={{
                            background: 'var(--tooltip-bg)',
                            border: '1px solid var(--tooltip-border)',
                            borderRadius: 10,
                            fontSize: 12,
                        }}
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        formatter={(value: any, name: any) => {
                            if (value === undefined || name === 'band_lower' || name === 'band_upper') return null;
                            const labels: Record<string, string> = {
                                actual: t('analytics_avg_price_label', 'Avg Price'),
                                predicted: t('analytics_forecast_predicted', 'Forecast'),
                            };
                            return [formatPrice(value as number), labels[name as string] ?? name] as [string, string];
                        }}
                        labelFormatter={(label: unknown) => {
                            const d = new Date(String(label));
                            return d.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' });
                        }}
                    />

                    <Legend
                        formatter={(value: string) => {
                            const map: Record<string, string> = {
                                actual: t('analytics_avg_price_label', 'Actual avg price'),
                                predicted: t('analytics_forecast_predicted', 'Forecast (±1σ)'),
                            };
                            return map[value] ?? value;
                        }}
                    />

                    {/* Confidence band (lower → upper) */}
                    <Area
                        type="monotone"
                        dataKey="lower"
                        stroke="none"
                        fill="none"
                        legendType="none"
                        tooltipType="none"
                        name="band_lower"
                        dot={false}
                        activeDot={false}
                    />
                    <Area
                        type="monotone"
                        dataKey="upper"
                        stroke="none"
                        fill="url(#forecastBand)"
                        legendType="none"
                        tooltipType="none"
                        name="band_upper"
                        dot={false}
                        activeDot={false}
                        // Stack above lower to create the band
                        baseValue="dataMin"
                    />

                    {/* Actual historical line */}
                    <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#5bc0c4"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                        name="actual"
                        connectNulls
                    />

                    {/* Forecast dashed line */}
                    <Line
                        type="monotone"
                        dataKey="predicted"
                        stroke="#b4ebca"
                        strokeWidth={2}
                        strokeDasharray="6 3"
                        dot={false}
                        activeDot={{ r: 4 }}
                        name="predicted"
                        connectNulls
                    />

                    {/* "Today" divider */}
                    {todayDate && (
                        <ReferenceLine
                            x={todayDate}
                            stroke="var(--text-muted)"
                            strokeDasharray="4 2"
                            strokeWidth={1}
                            label={{
                                value: t('analytics_forecast_today', 'Today'),
                                position: 'insideTopRight',
                                fontSize: 10,
                                fill: 'var(--text-muted)',
                            }}
                        />
                    )}
                </ComposedChart>
            </ResponsiveContainer>

            <p className="text-xs text-text-muted mt-3">
                ⚠ {t('analytics_forecast_disclaimer',
                    'Forecast is a linear extrapolation only. Do not use for financial decisions.')}
            </p>
        </div>
    );
};

export default PriceForecastChart;
