import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell,
    AreaChart, Area,
    CartesianGrid, Legend
} from 'recharts';
import { fetchStats, type StatsData } from '../services/api';

const CHART_COLORS = ['#4F46E5', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];

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
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
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

    return (
        <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-surface rounded-xl border border-border p-6 text-center">
                    <p className="text-3xl font-bold text-primary">{stats.total_listings.toLocaleString()}</p>
                    <p className="text-sm text-text-muted mt-1">{t('analytics_total')}</p>
                </div>
                <div className="bg-surface rounded-xl border border-border p-6 text-center">
                    <p className="text-3xl font-bold text-primary">${stats.avg_price_usd.toLocaleString()}</p>
                    <p className="text-sm text-text-muted mt-1">{t('analytics_avg_price')}</p>
                </div>
                <div className="bg-surface rounded-xl border border-border p-6 text-center">
                    <p className="text-3xl font-bold text-primary">{stats.avg_area} {t('area_unit')}</p>
                    <p className="text-sm text-text-muted mt-1">{t('analytics_avg_area')}</p>
                </div>
            </div>

            {/* Charts Row 1: City + Rooms */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* By City */}
                <div className="bg-surface rounded-xl border border-border p-6">
                    <h3 className="text-lg font-semibold text-text-main mb-4">{t('analytics_by_city')}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={stats.by_city} layout="vertical" margin={{ left: 80 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                            <XAxis type="number" tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} />
                            <YAxis type="category" dataKey="city" tick={{ fill: 'var(--color-text-main)', fontSize: 12 }} width={75} />
                            <Tooltip
                                contentStyle={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                                formatter={((value: number) => [value, t('analytics_count')]) as any}
                            />
                            <Bar dataKey="count" fill="#4F46E5" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* By Rooms */}
                <div className="bg-surface rounded-xl border border-border p-6">
                    <h3 className="text-lg font-semibold text-text-main mb-4">{t('analytics_by_rooms')}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={stats.by_rooms}
                                dataKey="count"
                                nameKey="rooms"
                                cx="50%" cy="50%"
                                innerRadius={60}
                                outerRadius={110}
                                paddingAngle={2}
                                label={((entry: { name: string; value: number }) => `${entry.name}R: ${entry.value}`) as any}
                            >
                                {stats.by_rooms.map((_entry, index) => (
                                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                                formatter={((value: number, _name: string, props: { payload: { avg_price: number; rooms: number } }) => [
                                    `${value} (avg ${formatPrice(props.payload.avg_price)})`,
                                    `${props.payload.rooms} ${t('rooms')}`
                                ]) as any}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 2: Price Histogram + Trend */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Price Distribution */}
                <div className="bg-surface rounded-xl border border-border p-6">
                    <h3 className="text-lg font-semibold text-text-main mb-4">{t('analytics_price_dist')}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={stats.price_histogram}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                            <XAxis dataKey="range" tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} />
                            <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                            />
                            <Bar dataKey="count" fill="#0EA5E9" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Recent Trend */}
                <div className="bg-surface rounded-xl border border-border p-6">
                    <h3 className="text-lg font-semibold text-text-main mb-4">{t('analytics_trend')}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={stats.recent_trend}>
                            <defs>
                                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#4F46E5" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                            <XAxis dataKey="date" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                            <YAxis yAxisId="left" tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} />
                            <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} tickFormatter={formatPrice} />
                            <Tooltip
                                contentStyle={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                                formatter={((value: number, name: string) => [
                                    name === 'avg_price' ? formatPrice(value) : value,
                                    name === 'avg_price' ? t('analytics_avg_price') : t('analytics_count')
                                ]) as any}
                            />
                            <Legend />
                            <Area yAxisId="left" type="monotone" dataKey="count" stroke="#4F46E5" fill="url(#colorCount)" name={t('analytics_count')} />
                            <Area yAxisId="right" type="monotone" dataKey="avg_price" stroke="#10B981" fill="url(#colorPrice)" name={t('analytics_avg_price')} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
