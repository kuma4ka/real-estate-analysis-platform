import type { StatsData } from '../services/api';

interface ChartRefs {
    roomsRef: HTMLElement | null;
    cityRef: HTMLElement | null;
    priceDistRef: HTMLElement | null;
    trendRef: HTMLElement | null;
}

type TFunction = (key: string, fallback?: string) => string;

// ─── Helpers ────────────────────────────────────────────────────────────────

const formatPrice = (value: number) => {
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value}`;
};

const captureElement = async (
    el: HTMLElement,
    isDark: boolean
): Promise<string | null> => {
    try {
        const { default: html2canvas } = await import('html2canvas');
        const canvas = await html2canvas(el, {
            scale: 2,
            useCORS: true,
            backgroundColor: isDark ? '#1a1f2e' : '#ffffff',
            logging: false,
        });
        return canvas.toDataURL('image/png');
    } catch {
        return null;
    }
};

// ─── Main export function ────────────────────────────────────────────────────

export async function exportAnalyticsPdf(
    stats: StatsData,
    refs: ChartRefs,
    t: TFunction,
    lang: string
): Promise<void> {
    const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([
        import('jspdf'),
        import('jspdf-autotable'),
    ]);

    const isDark = document.documentElement.classList.contains('dark');
    const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });

    const pageW = doc.internal.pageSize.getWidth();
    const margin = 40;
    const contentW = pageW - margin * 2;
    let y = margin;

    // ── Color palette ──────────────────────────────────────────────────────
    const PRIMARY = [91, 192, 196] as [number, number, number];     // #5bc0c4
    const SURFACE = isDark ? [30, 36, 50] as [number, number, number] : [248, 250, 252] as [number, number, number];
    const TEXT    = isDark ? [220, 220, 230] as [number, number, number] : [30, 30, 40] as [number, number, number];
    const MUTED   = isDark ? [130, 140, 160] as [number, number, number] : [100, 110, 130] as [number, number, number];
    const BG      = isDark ? [15, 17, 23] as [number, number, number] : [255, 255, 255] as [number, number, number];

    // ── Background ─────────────────────────────────────────────────────────
    doc.setFillColor(...BG);
    doc.rect(0, 0, pageW, doc.internal.pageSize.getHeight(), 'F');

    // ── Header bar ─────────────────────────────────────────────────────────
    doc.setFillColor(...PRIMARY);
    doc.rect(0, 0, pageW, 60, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(22);
    doc.setTextColor(255, 255, 255);
    doc.text(t('app_title', 'Real Estate Analyzer'), margin, 38);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    const dateStr = new Date().toLocaleDateString(lang === 'uk' ? 'uk-UA' : 'en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
    });
    doc.text(dateStr, pageW - margin, 38, { align: 'right' });

    y = 80;

    // ── Section title helper ───────────────────────────────────────────────
    const sectionTitle = (title: string) => {
        doc.setDrawColor(...PRIMARY);
        doc.setLineWidth(2);
        doc.line(margin, y + 2, margin + 4, y + 2);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(13);
        doc.setTextColor(...TEXT);
        doc.text(title, margin + 10, y + 4);
        y += 20;
    };

    // Helper to read jsPDF-autotable's finalY (not in public types)
    const getTableFinalY = () =>
        (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY;


    // ── 1. Summary Cards ────────────────────────────────────────────────────
    sectionTitle(t('view_analytics', 'Analytics Overview'));

    const summaryData = [
        [t('analytics_total', 'Total Active'), stats.total_active.toLocaleString()],
        [t('analytics_avg_price', 'Avg Price'), `$${stats.avg_price.toLocaleString()}`],
        [t('analytics_avg_area', 'Avg Area'), `${stats.avg_area} m²`],
        [t('analytics_avg_price_m2', 'Avg Price/m²'), `$${stats.avg_price_per_m2?.toLocaleString() ?? '—'}/m²`],
    ];

    autoTable(doc, {
        startY: y,
        head: [],
        body: summaryData,
        margin: { left: margin, right: margin },
        styles: {
            fontSize: 11,
            cellPadding: 8,
            fillColor: SURFACE,
            textColor: TEXT,
            lineColor: PRIMARY,
            lineWidth: 0.3,
        },
        columnStyles: {
            0: { fontStyle: 'bold', cellWidth: contentW * 0.5, textColor: MUTED },
            1: { fontStyle: 'bold', textColor: PRIMARY, halign: 'right' },
        },
        theme: 'plain',
    });
    y = getTableFinalY() + 24;

    // ── 2. Chart: By Rooms (Donut) ─────────────────────────────────────────
    // Wait for charts to settle (React re-render with isAnimationActive=false)
    await new Promise(resolve => setTimeout(resolve, 400));

    if (refs.roomsRef) {
        sectionTitle(t('analytics_by_rooms', 'Distribution by Rooms'));
        const img = await captureElement(refs.roomsRef, isDark);
        if (img) {
            const imgH = (contentW / 2) * 0.7;
            if (y + imgH > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
            doc.addImage(img, 'PNG', margin, y, contentW / 2, imgH);
            y += imgH + 8;
        }
    }

    // ── 3. City breakdown ───────────────────────────────────────────────────
    if (y + 80 > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
    sectionTitle(t('analytics_city_metrics', 'By City'));

    if (refs.cityRef) {
        const img = await captureElement(refs.cityRef, isDark);
        if (img) {
            const imgH = contentW * 0.45;
            if (y + imgH > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
            doc.addImage(img, 'PNG', margin, y, contentW, imgH);
            y += imgH + 12;
        }
    }

    // City data table (searchable)
    autoTable(doc, {
        startY: y,
        head: [[
            t('city', 'City'),
            t('count', 'Count'),
            t('analytics_city_metric_price', 'Avg Price'),
            t('analytics_city_metric_m2', 'Avg Price/m²'),
        ]],
        body: stats.by_city.map(c => [
            c.city,
            c.count.toLocaleString(),
            `$${c.avg_price.toLocaleString()}`,
            `$${c.avg_price_per_m2?.toLocaleString() ?? '—'}`,
        ]),
        margin: { left: margin, right: margin },
        headStyles: { fillColor: PRIMARY, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 10 },
        bodyStyles: { fillColor: SURFACE, textColor: TEXT, fontSize: 10, cellPadding: 6 },
        alternateRowStyles: { fillColor: BG },
        theme: 'plain',
    });
    y = getTableFinalY() + 24;

    // ── 4. Price Range Distribution ─────────────────────────────────────────
    if (y + 80 > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
    sectionTitle(t('analytics_price_dist', 'Price Distribution'));

    if (refs.priceDistRef) {
        const img = await captureElement(refs.priceDistRef, isDark);
        if (img) {
            const imgH = contentW * 0.42;
            if (y + imgH > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
            doc.addImage(img, 'PNG', margin, y, contentW * 0.65, imgH);
            y += imgH + 12;
        }
    }

    autoTable(doc, {
        startY: y,
        head: [[t('analytics_price_dist', 'Range'), t('count', 'Count')]],
        body: stats.by_price_ranges.map(r => [r.range, r.count.toLocaleString()]),
        margin: { left: margin, right: margin },
        headStyles: { fillColor: PRIMARY, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 10 },
        bodyStyles: { fillColor: SURFACE, textColor: TEXT, fontSize: 10, cellPadding: 6 },
        alternateRowStyles: { fillColor: BG },
        theme: 'plain',
    });
    y = getTableFinalY() + 24;

    // ── 5. By Rooms — data table ─────────────────────────────────────────────
    if (y + 80 > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
    sectionTitle(t('analytics_by_rooms', 'By Rooms'));

    autoTable(doc, {
        startY: y,
        head: [[t('rooms', 'Rooms'), t('count', 'Count'), t('analytics_avg_price_label', 'Avg Price')]],
        body: stats.by_rooms.map(r => [
            r.rooms >= 4 ? '4+' : String(r.rooms),
            r.count.toLocaleString(),
            formatPrice(r.avg_price),
        ]),
        margin: { left: margin, right: margin },
        headStyles: { fillColor: PRIMARY, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 10 },
        bodyStyles: { fillColor: SURFACE, textColor: TEXT, fontSize: 10, cellPadding: 6 },
        alternateRowStyles: { fillColor: BG },
        theme: 'plain',
    });
    y = getTableFinalY() + 24;

    // ── 6. Trend chart ────────────────────────────────────────────────────────
    if (refs.trendRef) {
        if (y + 80 > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
        sectionTitle(t('analytics_trend', 'Recent Trend'));

        const img = await captureElement(refs.trendRef, isDark);
        if (img) {
            const imgH = contentW * 0.38;
            if (y + imgH > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
            doc.addImage(img, 'PNG', margin, y, contentW, imgH);
            y += imgH + 12;
        }
    }

    // ── Recent trend table ─────────────────────────────────────────────────
    if (stats.recent_trend.length > 0) {
        if (y + 80 > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }

        autoTable(doc, {
            startY: y,
            head: [['Date', t('count', 'Count'), t('analytics_avg_price_label', 'Avg Price'), '± %']],
            body: stats.recent_trend.slice(-10).map(r => [
                r.month,
                r.count.toLocaleString(),
                formatPrice(r.avg_price),
                r.price_change_pct !== null
                    ? `${r.price_change_pct > 0 ? '+' : ''}${r.price_change_pct.toFixed(1)}%`
                    : '—',
            ]),
            margin: { left: margin, right: margin },
            headStyles: { fillColor: PRIMARY, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 10 },
            bodyStyles: { fillColor: SURFACE, textColor: TEXT, fontSize: 10, cellPadding: 6 },
            alternateRowStyles: { fillColor: BG },
            theme: 'plain',
        });
    }

    // ── Footer on each page ────────────────────────────────────────────────
    const totalPages = (doc as unknown as { internal: { getNumberOfPages(): number } }).internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        const pageH = doc.internal.pageSize.getHeight();
        doc.setDrawColor(...PRIMARY);
        doc.setLineWidth(0.5);
        doc.line(margin, pageH - 28, pageW - margin, pageH - 28);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...MUTED);
        doc.text(t('app_title', 'Real Estate Analyzer'), margin, pageH - 16);
        doc.text(`${i} / ${totalPages}`, pageW - margin, pageH - 16, { align: 'right' });
    }

    // ── Save ───────────────────────────────────────────────────────────────
    const date = new Date().toISOString().slice(0, 10);
    doc.save(`analytics-${date}.pdf`);
}
