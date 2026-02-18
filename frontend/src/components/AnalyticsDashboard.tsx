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
    const { t } = useTranslation();
    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState(true);

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
    ];

    return (
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
                                data={stats.by_rooms}
                                dataKey="count"
                                nameKey="rooms"
                                cx="50%" cy="50%"
                                innerRadius={55}
                                outerRadius={100}
                                paddingAngle={3}
                                label={((entry: { name: string; value: number }) => `${entry.name}R: ${entry.value}`) as any}
                            >
                                {stats.by_rooms.map((_entry, index) => (
                                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                formatter={((value: number, _name: string, props: { payload: { avg_price: number; rooms: number } }) => [
                                    `${value} (avg ${formatPrice(props.payload.avg_price)})`,
                                    `${props.payload.rooms} ${t('rooms')}`
                                ]) as any}
                            />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* By City — Bar */}
                <div className="bg-surface rounded-xl border border-border p-5 shadow-card">
                    <h3 className="text-sm font-semibold text-text-main mb-4">{t('analytics_by_city')}</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={stats.by_city} layout="vertical" margin={{ left: 80 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                            <XAxis type="number" tick={{ fill: 'var(--chart-text)', fontSize: 12 }} />
                            <YAxis type="category" dataKey="city" tick={{ fill: 'var(--chart-text-bold)', fontSize: 12 }} width={75} />
                            <Tooltip
                                contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '10px', fontSize: 13 }}
                                formatter={((value: number) => [value, t('analytics_count')]) as any}
                            />
                            <Bar dataKey="count" fill="#5bc0c4" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 2: Price Histogram + Trend */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
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
                            />
                            <Bar dataKey="count" fill="#b4ebca" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Recent Trend */}
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
                                formatter={((value: number, name: string) => [
                                    name === 'avg_price' ? formatPrice(value) : value,
                                    name === 'avg_price' ? t('analytics_avg_price') : t('analytics_count')
                                ]) as any}
                            />
                            <Legend />
                            <Area yAxisId="left" type="monotone" dataKey="count" stroke="#5bc0c4" fill="url(#colorCount)" name={t('analytics_count')} />
                            <Area yAxisId="right" type="monotone" dataKey="avg_price" stroke="#ffb7c3" fill="url(#colorPrice)" name={t('analytics_avg_price')} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
