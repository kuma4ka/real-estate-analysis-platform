import React from 'react';
import type { Property } from '../types/property';
import { useTranslation } from 'react-i18next';

interface PropertyCardProps {
    property: Property;
}

const PropertyCard: React.FC<PropertyCardProps> = ({ property }) => {
    const { t } = useTranslation();

    const formattedPrice = new Intl.NumberFormat('uk-UA', {
        style: 'currency',
        currency: property.currency || 'USD',
        maximumFractionDigits: 0,
    }).format(property.price);

    const imageUrl = (property.images && property.images.length > 0) ? property.images[0] : null;

    return (
        <a
            href={property.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-surface rounded-xl shadow-card hover:shadow-card-hover transition-all duration-300 overflow-hidden border border-border flex flex-col h-full group"
        >
            {/* Image */}
            <div className="h-44 bg-background relative overflow-hidden">
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={property.title}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        loading="lazy"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full text-text-muted bg-background">
                        <svg className="w-10 h-10 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </div>
                )}

                {property.rooms && (
                    <div className="absolute top-2.5 right-2.5 bg-surface/90 backdrop-blur-sm text-text-main text-xs font-semibold px-2 py-1 rounded-md">
                        {property.rooms} {t('rooms')}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-4 flex flex-col flex-grow">
                <h3 className="text-base font-bold text-text-main line-clamp-2 leading-snug mb-2" title={property.title}>
                    {property.title}
                </h3>

                <p className="text-sm text-text-muted mb-2">
                    {property.address || property.city || '—'}
                </p>

                <div className="border-t border-border pt-3 mt-auto">
                    <div className="flex items-center justify-between text-sm text-text-muted">
                        <span>{property.area ? `${property.area} ${t('area_unit')}` : '—'}</span>
                        <span className="font-bold text-base text-text-main">{formattedPrice}</span>
                    </div>
                </div>
            </div>
        </a>
    );
};

export default PropertyCard;