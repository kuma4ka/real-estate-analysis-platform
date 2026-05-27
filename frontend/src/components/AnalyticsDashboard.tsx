import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell,
    AreaChart, Area,
    CartesianGrid, Legend,
    type PieLabelRenderProps,
} from 'recharts';
import type { ValueType, NameType, Payload } from 'recharts/types/component/DefaultTooltipContent';

// Typed shapes used in Recharts label/formatter callbacks.
// Pie label receives PieLabelRenderProps & the data item merged in at runtime.
type RoomLabelProps      = PieLabelRenderProps & { rooms: number; count: number };
type PriceRangeLabelProps = PieLabelRenderProps & { range: string };
type ActiveLabelProps    = PieLabelRenderProps & { name: string; value: number };
interface TrendPayload { price_change_pct?: number | null }
import { fetchStats, type StatsData } from '../services/api';
import { useAuth } from '../context/AuthContext';
import useThrottle from '../hooks/useThrottle';
import { exportAnalyticsPdf } from '../utils/exportAnalyticsPdf';
import PriceForecastChart from './PriceForecastChart';
import { UserRole } from '../types/user';
import { formatPrice } from '../utils/format';

const CHART_COLORS = ['#5bc0c4', '#b4ebca', '#d9f2b4', '#ffb7c3', '#d3fac7', '#9ed8db', '#a8d5ba', '#ffd4dc'];

const AnalyticsDashboard: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { user } = useAuth();
    // Per-chart refs for selective canvas capture
    const roomsRef    = useRef<HTMLDivElement>(null);
    const cityRef     = useRef<HTMLDivElement>(null);
    const priceDistRef = useRef<HTMLDivElement>(null);
    const trendRef    = useRef<HTMLDivElement>(null);
    const forecastRef = useRef<HTMLDivElement>(null);

    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const [exportError, setExportError] = useState<string | null>(null);
    const [drilldownOpen, setDrilldownOpen] = useState(false);
    const [cityMetric, setCityMetric] = useState<'count' | 'avg_price' | 'avg_price_per_m2'>('count');

    const canExport = user?.role === UserRole.ANALYST || user?.role === UserRole.ADMIN;

    const exportPdfCore = async () => {
        if (isExporting) return;
        setIsExporting(true);
        setExportError(null);
        try {
            if (!stats) throw new Error('No data loaded');
            await exportAnalyticsPdf(
                stats,
                {
                    roomsRef: roomsRef.current,
                    cityRef: cityRef.current,
                    priceDistRef: priceDistRef.current,
                    trendRef: trendRef.current,
                    forecastRef: forecastRef.current,
                },
                // Always use English for jsPDF — built-in Helvetica doesn't support Cyrillic
                (key, fallback) => {
                    const tEn = i18n.getFixedT('en');
                    return tEn(key) as string || fallback || key;
                }
            );
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'PDF export failed';
            setExportError(msg);
            // Auto-dismiss error after 4 seconds
            setTimeout(() => setExportError(null), 4_000);
        } finally {
            setIsExporting(false);
        }
    };

    const handleExportPdf = useThrottle(exportPdfCore, 10_000);

    // Translate city name from Ukrainian DB value to active locale
    const translateCity = (name: string): string => {
        if (i18n.language === 'uk') return name;
        const translated = t(`cities.${name}`, { defaultValue: '' });
        return translated || name;
    };

    useEffect(() => {
        const load = async () => {
            try {
                const data = await fetchStats();
                setStats(data);
            } catch {
                // Stats failed to load — UI shows empty state
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent"></div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="text-center py-20 text-text-muted">
                {t('analytics_error')}
            </div>
        );
    }

    const summaryCards = [
        { label: t('analytics_total'), value: stats.total_active.toLocaleString(), color: 'text-primary' },
        { label: t('analytics_avg_price'), value: `$${stats.avg_price.toLocaleString()}`, color: 'text-[#5bc0c4]' },
        { label: t('analytics_avg_area'), value: `${stats.avg_area} ${t('area_unit')}`, color: 'text-[#49adb1]' },
        { label: t('analytics_avg_price_m2'), value: `$${stats.avg_price_per_m2?.toLocaleString() ?? '—'}/m²`, color: 'text-[#b4ebca]' },
    ];

    // Group rooms: 1, 2, 3, then bucket everything 4+ together
    type RoomEntry = { rooms: number; count: number; avg_price: number };
    const rawRooms: RoomEntry[] = stats?.by_rooms ?? [];
    const mainRooms = rawRooms.filter(r => r.rooms <= 3);
    const extraRooms = rawRooms.filter(r => r.rooms >= 4);
    const groupedRooms = [
        ...mainRooms,
        ...(extraRooms.length > 0 ? [{
            rooms: 99 as number,
            count: extraRooms.reduce((s, r) => s + r.count, 0),
            avg_price: extraRooms.reduce((s, r) => s + r.avg_price * r.count, 0) /
                       extraRooms.reduce((s, r) => s + r.count, 0),
        }] : []),
    ];
    const roomLabel = (rooms: number) => rooms === 99 ? '4+' : String(rooms);

    return (
        <div className="space-y-6">

            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-text-main">
                    {t('view_analytics')}
                </h2>
                {canExport && (
                    <button
                        onClick={handleExportPdf}
                        disabled={isExporting}
                        className="
                            flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                            bg-primary text-white
                            hover:bg-primary-hover
                            disabled:opacity-50 disabled:cursor-not-allowed
                            transition-all duration-200
                        "
                    >
                        {isExporting ? (
                            <>
                                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                {t('analytics_export_loading', 'Generating PDF...')}
                            </>
                        ) : (
                            <>
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                {t('analytics_export_pdf', 'Download PDF')}
                            </>
                        )}
                    </button>
                )}
            </div>


            {exportError && (
                <div className="flex items-center gap-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg px-4 py-3 text-sm">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                    </svg>
                    <span className="flex-1">{exportError}</span>
                    <button onClick={() => setExportError(null)} className="hover:opacity-70 transition-opacity">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            )}


            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {summaryCards.map((card, i) => (
                    <div key={i} className="bg-surface rounded-xl border border-border p-5 shadow-card">
                        <p className="text-sm text-text-muted mb-1">{card.label}</p>
                        <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                    </div>
                ))}
            </div>


            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                <div ref={roomsRef} className="bg-surface rounded-xl border border-border p-5 shadow-card">
                    <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_by_rooms')}</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={groupedRooms}
                                dataKey="count"
                                nameKey="rooms"
                                cx="50%"
                                cy="50%"
                                innerRadius={55}
                                outerRadius={100}
                                paddingAngle={3}
                                isAnimationActive={!isExporting}
                                label={((entry: RoomLabelProps) => `${roomLabel(entry.rooms)}R: ${entry.count}`) as unknown as PieLabelRenderProps}
                                onClick={(_data: unknown, index: number) => {
                                    if (groupedRooms[index]?.rooms === 99) setDrilldownOpen(true);
                                }}
                            >
                                {groupedRooms.map((_entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                                        className={_entry.rooms === 99 ? 'cursor-pointer hover:opacity-80' : ''}
                                    />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelStyle={{ color: 'var(--chart-text-bold)' }}
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                formatter={(value: any, _name: any, props: Payload<ValueType, NameType>) => [
                                    (props.payload as RoomEntry)?.rooms === 99
                                        ? `${value} — ${t('analytics_click_details')}`
                                        : `${value} ${t('rooms')}`,
                                    t('count')
                                ] as [string, string]}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>


                <div ref={cityRef} className="bg-surface p-6 rounded-xl border border-border flex flex-col h-full">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-semibold text-text-main">{t('analytics_city_metrics')}</h3>
                        <select
                            className="bg-background border border-border text-text-main text-sm rounded-lg pr-8 focus:ring-primary focus:border-primary p-2"
                            value={cityMetric}
                            onChange={(e) => setCityMetric(e.target.value as 'count' | 'avg_price' | 'avg_price_per_m2')}
                        >
                            <option value="count">{t('analytics_city_metric_count')}</option>
                            <option value="avg_price">{t('analytics_city_metric_price')}</option>
                            <option value="avg_price_per_m2">{t('analytics_city_metric_m2')}</option>
                        </select>
                    </div>
                    <div className="flex-grow min-h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={stats.by_city} layout="vertical" margin={{ left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                                <XAxis
                                    type="number"
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={(val) => {
                                        if (cityMetric === 'count') return val;
                                        if (cityMetric === 'avg_price_per_m2') return `$${val}`;
                                        return `$${val / 1000}k`;
                                    }}
                                    tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
                                />
                                <YAxis
                                    type="category"
                                    dataKey="city"
                                    width={155}
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={translateCity}
                                    tick={{ fill: 'var(--chart-text)', fontSize: 12 }}
                                />
                                <Tooltip
                                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                formatter={(value: any) => {
                                        if (cityMetric === 'count') return [value, t('analytics_city_metric_count')];
                                        if (cityMetric === 'avg_price_per_m2') return [`$${value}/m²`, t('analytics_city_metric_m2')];
                                        return [formatPrice(value as number), t('analytics_city_metric_price')];
                                    }}
                                />
                                <Bar
                                    dataKey={cityMetric}
                                    fill={cityMetric === 'count' ? '#5bc0c4' : cityMetric === 'avg_price' ? '#b4ebca' : '#d9f2b4'}
                                    radius={[0, 4, 4, 0]}
                                    isAnimationActive={!isExporting}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>


            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                <div ref={priceDistRef} className="bg-surface p-6 rounded-xl border border-border shadow-sm flex flex-col h-full">
                    <h3 className="text-lg font-semibold text-text-main mb-6">{t('analytics_price_dist')}</h3>
                    <div className="flex-grow min-h-[420px] flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
                                <Pie
                                    data={stats?.by_price_ranges}
                                    dataKey="count"
                                    nameKey="range"
                                    cx="50%"
                                    cy="50%"
                                    outerRadius={95}
                                    fill="#8884d8"
                                    isAnimationActive={!isExporting}
                                    label={((entry: PriceRangeLabelProps) => entry.range) as unknown as PieLabelRenderProps}
                                >
                                    {stats?.by_price_ranges?.map((_entry, index) => (
                                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                    itemStyle={{ color: 'var(--chart-text-bold)' }}
                                />
                                <Legend wrapperStyle={{ fontSize: 12, paddingTop: '20px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>


                <div className="bg-surface p-6 rounded-xl border border-border shadow-sm flex flex-col h-full">
                    <h3 className="text-lg font-semibold text-text-main mb-6">{t('analytics_status_dist')}</h3>
                    <div className="flex-grow min-h-[300px] flex items-center justify-center">
                        <div className="relative w-full h-full flex flex-col items-center justify-center">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={[{ name: 'Active', value: stats?.total_active ?? 0 }]}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={80}
                                        outerRadius={110}
                                        fill="#82ca9d"
                                        isAnimationActive={!isExporting}
                                        label={((entry: ActiveLabelProps) => `${entry.name ?? ''}: ${entry.value ?? ''}`) as unknown as PieLabelRenderProps}
                                    >
                                        <Cell fill={CHART_COLORS[0]} />
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                        itemStyle={{ color: 'var(--chart-text-bold)' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                <span className="text-3xl font-bold text-text-main">{stats?.total_active ?? 0}</span>
                                <span className="text-sm text-text-muted">{t('analytics_total_active')}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>


            <div ref={trendRef} className="bg-surface rounded-xl border border-border p-5 shadow-card">
                <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_trend')}</h3>
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={stats?.recent_trend}>
                        <defs>
                            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#5bc0c4" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#5bc0c4" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--chart-grid)" />
                        <XAxis
                            dataKey="month"
                            tickFormatter={(val) => {
                                const d = new Date(val);
                                return `${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`;
                            }}
                            tick={{ fill: 'var(--chart-text)', fontSize: 12 }}
                            minTickGap={20}
                        />
                        <YAxis yAxisId="left" tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            tickFormatter={formatPrice}
                            tick={{ fill: 'var(--chart-text)', fontSize: 12 }}
                        />
                        <Tooltip
                            contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                            itemStyle={{ color: 'var(--chart-text-bold)' }}
                            labelStyle={{ color: 'var(--chart-text-bold)' }}
                            labelFormatter={(val) => {
                                const d = new Date(String(val));
                                return `${d.toLocaleString('default', { month: 'long' })} ${d.getFullYear()}`;
                            }}
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                            formatter={(value: any, _name: any, props: Payload<ValueType, NameType>) => {
                                const dataKey = (props as { dataKey?: string }).dataKey;
                                const payload = (props.payload ?? {}) as TrendPayload;
                                const isPrice = dataKey === 'avg_price';
                                if (isPrice && payload.price_change_pct != null) {
                                    const pctC = payload.price_change_pct;
                                    const sign = pctC > 0 ? '+' : '';
                                    return [`${formatPrice(value as number)} (${sign}${pctC.toFixed(1)}%)`, t('analytics_avg_price_label')];
                                }
                                return isPrice ? [formatPrice(value as number), t('analytics_avg_price_label')] : [value, t('count')];
                            }}
                        />
                        <Legend />
                        <Area yAxisId="left" type="monotone" dataKey="count" stroke="#5bc0c4" fillOpacity={1} fill="url(#colorCount)" name={t('count')} strokeWidth={2} isAnimationActive={!isExporting} />
                        <Area yAxisId="right" type="monotone" dataKey="avg_price" stroke="#b4ebca" fill="none" name={t('avg_price')} strokeWidth={2} isAnimationActive={!isExporting} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>


            <div ref={forecastRef}>
                <PriceForecastChart isExporting={isExporting} />
            </div>


            {drilldownOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <div className="bg-surface rounded-xl border border-border p-6 max-w-md w-full shadow-2xl">
                        <h3 className="text-xl font-bold text-text-main mb-4">{t('analytics_4plus_details')}</h3>
                        <div className="space-y-3 mb-6">
                            {extraRooms.map(r => (
                                <div key={r.rooms} className="flex justify-between items-center border-b border-border pb-2">
                                    <span className="text-text-main font-medium">{r.rooms} {t('rooms')}</span>
                                    <div className="text-right">
                                        <div className="text-primary font-bold">{r.count} {t('analytics_count')}</div>
                                        <div className="text-sm text-text-muted">avg: {formatPrice(r.avg_price)}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <button
                            onClick={() => setDrilldownOpen(false)}
                            className="w-full bg-border text-text-main hover:bg-[#d1d5db] dark:hover:bg-[#4b5563] font-medium py-2 rounded-lg transition-colors"
                        >
                            {t('analytics_close')}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnalyticsDashboard;
