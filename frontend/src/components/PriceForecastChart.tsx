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
import { fetchForecast, type ForecastData, type ForecastPoint, type ForecastHistoricalPoint } from '../services/api';

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

interface Props {
    isExporting?: boolean;
}

const PriceForecastChart: React.FC<Props> = ({ isExporting = false }) => {
    const { t } = useTranslation();
    const [forecast, setForecast] = useState<ForecastData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string>('');

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchForecast(selectedCity || undefined);
                if (!cancelled) setForecast(data);
            } catch (err: unknown) {
                if (!cancelled) setError(err instanceof Error ? err.message : 'Forecast unavailable');
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        void load();
        return () => { cancelled = true; };
    }, [selectedCity]);

    if (!forecast && loading) {
        return (
            <div className="bg-surface rounded-xl border border-border p-5 shadow-card animate-pulse">
                <div className="h-4 bg-border rounded w-48 mb-4" />
                <div className="h-64 bg-border rounded" />
            </div>
        );
    }

    // If we have nothing at all (e.g. initial network failure)
    if (!forecast && error) {
        return (
            <div className="bg-surface rounded-xl border border-border p-5 shadow-card h-[380px] flex items-center justify-center">
                <p className="text-text-muted">{error}</p>
            </div>
        );
    }

    const hasDataError = error || forecast?.error;
    const hasData = !hasDataError && forecast && forecast.historical.length > 0 && forecast.forecast.length > 0;


    type ChartPoint = {
        date: string;
        actual?: number;
        predicted?: number;
        band?: [number, number];   // [lower, upper] encoded as area range
        lower?: number;
        upper?: number;
        isForecast?: boolean;
    };

    let data: ChartPoint[] = [];
    let todayDate: string | undefined;
    let fitLabel = '', fitColor = '', trend = '', trendColor = '';

    if (hasData && forecast) {
        const historical: ChartPoint[] = forecast.historical.map((r: ForecastHistoricalPoint) => ({
            date: r.date,
            actual: r.avg_price,
        }));

        const lastHist = historical[historical.length - 1];
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

        data = [...historical, bridgePoint, ...forecastPoints];

        todayDate = historical[historical.length - 1]?.date;

        const fit = rSquaredLabel(forecast.r_squared, t);
        fitLabel = fit.label;
        fitColor = fit.color;
        
        trend = forecast.slope_per_day >= 0 ? '↑' : '↓';
        trendColor = forecast.slope_per_day >= 0 ? 'text-emerald-400' : 'text-red-400';
    }

    return (
        <div className="bg-surface rounded-xl border border-border p-5 shadow-card">

            <div className="flex items-start justify-between mb-4 flex-wrap gap-4">
                <div>
                     <h3 className="text-sm font-semibold text-text-main pb-1">
                        {t('analytics_forecast_title', 'Price Forecast — next 30 days')}
                    </h3>
                    <div className="flex items-center gap-3">
                        <select
                            value={selectedCity}
                            onChange={(e) => setSelectedCity(e.target.value)}
                            disabled={loading}
                            className="bg-background border border-border text-text-main text-xs rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary shadow-sm"
                        >
                            <option value="">{t('analytics_forecast_city_all', 'All Cities (Global)')}</option>
                            {forecast?.available_cities?.map(c => (
                                <option key={c} value={c}>{t(`cities.${c}`, c)}</option>
                            ))}
                        </select>
                        {loading && <span className="text-xs text-text-muted animate-pulse">{t('loading')}</span>}
                    </div>
                </div>


                {hasData && forecast && (
                    <div className="flex items-center gap-3 text-xs font-mono">
                        <div className="flex flex-col items-end">
                            <span className="text-text-muted">R²</span>
                            <span className={`font-bold ${fitColor}`}>
                                {forecast.r_squared.toFixed(3)}
                                <span className="ml-1 font-normal text-text-muted">({fitLabel})</span>
                            </span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-text-muted">{t('analytics_forecast_trend', 'Trend/day')}</span>
                            <span className={`font-bold ${trendColor}`}>
                                {trend} {formatPrice(Math.abs(forecast.slope_per_day))}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {hasData ? (
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
                        isAnimationActive={!isExporting}
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
                        isAnimationActive={!isExporting}
                        // Stack above lower to create the band
                        baseValue="dataMin"
                    />


                    <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#5bc0c4"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                        name="actual"
                        connectNulls
                        isAnimationActive={!isExporting}
                    />


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
                        isAnimationActive={!isExporting}
                    />


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
            ) : (
                <div className="flex items-center justify-center h-[300px]">
                    <p className="text-text-muted">
                        {hasDataError || t('analytics_forecast_unavailable', 'Forecast data unavailable')}
                    </p>
                </div>
            )}

            <p className="text-xs text-text-muted mt-3">
                ⚠ {t('analytics_forecast_disclaimer',
                    'Forecast is a linear extrapolation only. Do not use for financial decisions.')}
            </p>
        </div>
    );
};

export default PriceForecastChart;
