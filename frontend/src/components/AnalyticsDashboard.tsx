import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell,
    AreaChart, Area,
    CartesianGrid, Legend
} from 'recharts';
import { fetchStats, type StatsData } from '../services/api';

const CHART_COLORS = ['#5bc0c4', '#b4ebca', '#d9f2b4', '#ffb7c3', '#d3fac7', '#9ed8db', '#a8d5ba', '#ffd4dc'];

const formatPrice = (value: number) => {
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value}`;
};

const AnalyticsDashboard: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [drilldownOpen, setDrilldownOpen] = useState(false);
    const [cityMetric, setCityMetric] = useState<'count' | 'avg_price' | 'avg_price_per_m2'>('count');

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
            } catch (err) {
                console.error('Failed to load stats', err);
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
        { label: t('analytics_total'), value: stats.total_listings.toLocaleString(), color: 'text-primary' },
        { label: t('analytics_avg_price'), value: `$${stats.avg_price_usd.toLocaleString()}`, color: 'text-[#5bc0c4]' },
        { label: t('analytics_avg_area'), value: `${stats.avg_area} ${t('area_unit')}`, color: 'text-[#49adb1]' },
        { label: t('analytics_avg_price_m2'), value: `$${stats.avg_price_per_m2?.toLocaleString() ?? '—'}/m²`, color: 'text-[#b4ebca]' },
    ];

    // Group rooms: 1, 2, 3, then bucket everything 4+ together
    type RoomEntry = { rooms: number; count: number; avg_price: number };
    const rawRooms: RoomEntry[] = stats.by_rooms ?? [];
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
        <>
        <div className="space-y-6">
            {/* Page Title */}
            <h2 className="text-2xl font-bold text-text-main">
                {t('view_analytics')}
            </h2>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {summaryCards.map((card, i) => (
                    <div key={i} className="bg-surface rounded-xl border border-border p-5 shadow-card">
                        <p className="text-sm text-text-muted mb-1">{card.label}</p>
                        <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                    </div>
                ))}
            </div>

            {/* Charts Row 1: Donut + Bar */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {/* By Rooms — Donut */}
                <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                    <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_by_rooms')}</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={groupedRooms}
                                dataKey="count"
                                nameKey="rooms"
                                cx="50%" cy="50%"
                                innerRadius={55}
                                outerRadius={100}
                                paddingAngle={3}
                                label={((entry: { name: number; value: number }) => `${roomLabel(entry.name)}R: ${entry.value}`) as any}
                                onClick={(_data: any, index: number) => {
                                    if (groupedRooms[index]?.rooms === 99) setDrilldownOpen(true);
                                }}
                                style={{ cursor: 'pointer' }}
                            >
                                {groupedRooms.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                                        opacity={entry.rooms === 99 ? 1 : 0.9}
                                        stroke={entry.rooms === 99 ? '#fff' : 'none'}
                                        strokeWidth={entry.rooms === 99 ? 2 : 0}
                                    />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelStyle={{ color: 'var(--chart-text-bold)' }}
                                formatter={((value: number, _name: string, props: { payload: { avg_price: number; rooms: number } }) => [
                                    props.payload.rooms === 99
                                        ? `${value} — ${t('analytics_click_details')}`
                                        : `${value} (avg ${formatPrice(props.payload.avg_price)})`,
                                    `${roomLabel(props.payload.rooms)} ${t('rooms')}`
                                ]) as any}
                            />
                            <Legend formatter={(value: any) => roomLabel(Number(value))} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* By City — Bar */}
                <div className="bg-surface rounded-xl border border-border p-5 shadow-card flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-sm font-semibold text-text-main">{t('analytics_by_city')}</h3>
                        <div className="flex gap-1 bg-background p-1 rounded-lg border border-border">
                            <button
                                onClick={() => setCityMetric('count')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${cityMetric === 'count' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                            >
                                {t('analytics_city_metric_count')}
                            </button>
                            <button
                                onClick={() => setCityMetric('avg_price')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${cityMetric === 'avg_price' ? 'bg-[#5bc0c4] text-white' : 'text-text-muted hover:text-text-main'}`}
                            >
                                {t('analytics_city_metric_price')}
                            </button>
                            <button
                                onClick={() => setCityMetric('avg_price_per_m2')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${cityMetric === 'avg_price_per_m2' ? 'bg-[#b4ebca] text-white' : 'text-text-muted hover:text-text-main'}`}
                            >
                                {t('analytics_city_metric_m2')}
                            </button>
                        </div>
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={stats.by_city} layout="vertical" margin={{ left: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis type="number" tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <YAxis
                                type="category"
                                dataKey="city"
                                tick={{ fill: 'var(--chart-text-bold)', fontSize: 11 }}
                                width={140}
                                tickFormatter={translateCity}
                            />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelStyle={{ color: 'var(--chart-text-bold)' }}
                                labelFormatter={(label) => translateCity(String(label))}
                                formatter={((value: number) => {
                                    if (cityMetric === 'count') return [value, t('analytics_city_metric_count')];
                                    if (cityMetric === 'avg_price_per_m2') return [`$${value}/m²`, t('analytics_city_metric_m2')];
                                    return [formatPrice(value), t('analytics_city_metric_price')];
                                }) as any}
                            />
                            <Bar 
                                dataKey={cityMetric} 
                                fill={cityMetric === 'count' ? '#5bc0c4' : cityMetric === 'avg_price' ? '#b4ebca' : '#d9f2b4'} 
                                radius={[0, 4, 4, 0]} 
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 2: Price by Rooms + Price Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {/* Price by Rooms */}
                <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                    <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_price_by_rooms')}</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={stats.by_rooms} margin={{ top: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis dataKey="rooms" tickFormatter={(v: number) => `${v}к`} tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <YAxis tick={{ fill: 'var(--chart-text)', fontSize: 12 }} tickFormatter={formatPrice} />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelFormatter={(label) => `${label} ${t('rooms')}`}
                                formatter={((value: number) => [formatPrice(value), t('analytics_avg_price_label')]) as any}
                            />
                            <Bar dataKey="avg_price" fill="#b4ebca" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Price Distribution */}
                <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                    <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_price_dist')}</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={stats.price_histogram}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis dataKey="range" tick={{ fill: 'var(--chart-text)', fontSize: 11 }} />
                            <YAxis tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelStyle={{ color: 'var(--chart-text-bold)' }}
                            />
                            <Bar dataKey="count" fill="#b4ebca" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 3: Recent Trend (Full width) */}
            <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_trend')}</h3>
                <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={stats.recent_trend}>
                            <defs>
                                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#5bc0c4" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#5bc0c4" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ffb7c3" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ffb7c3" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis dataKey="date" tick={{ fill: 'var(--chart-text)', fontSize: 10 }} />
                            <YAxis yAxisId="left" tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--chart-text)', fontSize: 12 }} tickFormatter={formatPrice} />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                labelStyle={{ color: 'var(--chart-text-bold)' }}
                                formatter={((value: number, _name: string, props: { dataKey: string, payload: { price_change_pct: number | null } }) => {
                                    const isPrice = props.dataKey === 'avg_price';
                                    if (isPrice && props.payload.price_change_pct !== null) {
                                        const change = props.payload.price_change_pct;
                                        const sign = change > 0 ? '+' : '';
                                        return [`${formatPrice(value)} (${sign}${change}%)`, t('analytics_avg_price')];
                                    }
                                    return [
                                        isPrice ? formatPrice(value) : value,
                                        isPrice ? t('analytics_avg_price') : t('analytics_count'),
                                    ];
                                }) as any}
                            />
                            <Legend />
                            <Area yAxisId="left" type="monotone" dataKey="count" stroke="#5bc0c4" fill="url(#colorCount)" name={t('analytics_count')} />
                            <Area yAxisId="right" type="monotone" dataKey="avg_price" stroke="#ffb7c3" fill="url(#colorPrice)" name={t('analytics_avg_price')} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
        </div>

        {/* 4+ Drilldown Modal */}
        {drilldownOpen && (
            <div
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                onClick={() => setDrilldownOpen(false)}
            >
                <div
                    className="bg-surface rounded-2xl border border-border p-6 shadow-2xl w-full max-w-lg mx-4"
                    onClick={e => e.stopPropagation()}
                >
                    <div className="flex items-center justify-between mb-5">
                        <h3 className="text-base font-bold text-text-main">
                            {t('analytics_4plus_title')}
                        </h3>
                        <button
                            onClick={() => setDrilldownOpen(false)}
                            className="text-text-muted hover:text-text-main transition-colors text-xl leading-none"
                            aria-label="Close"
                        >
                            ✕
                        </button>
                    </div>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={extraRooms} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis dataKey="rooms" tickFormatter={(v: number) => `${v}к`} tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <YAxis tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                itemStyle={{ color: 'var(--chart-text-bold)' }}
                                formatter={((value: number, name: string, props: { payload: { avg_price: number } }) => [
                                    name === 'count'
                                        ? `${value} (avg ${formatPrice(props.payload.avg_price)})`
                                        : formatPrice(value),
                                    name === 'count' ? t('analytics_count_label') : t('analytics_avg_price_label')
                                ]) as any}
                            />
                            <Bar dataKey="count" fill="#b4ebca" radius={[4, 4, 0, 0]} name="count" />
                        </BarChart>
                    </ResponsiveContainer>
                    <p className="text-xs text-text-muted mt-3 text-center">
                        {t('analytics_4plus_count', { count: extraRooms.reduce((s, r) => s + r.count, 0) })}
                    </p>
                </div>
            </div>
        )}
        </>
    );

};

export default AnalyticsDashboard;
