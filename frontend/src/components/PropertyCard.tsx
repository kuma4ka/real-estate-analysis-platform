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
        <div className="bg-surface rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden border border-border flex flex-col h-full group">
            {/* Image Area */}
            <div className="h-48 bg-background relative overflow-hidden">
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={property.title}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        loading="lazy"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full text-text-muted bg-gray-100 dark:bg-gray-800">
                        <span className="text-sm">No Image</span>
                    </div>
                )}
                
                <div className="absolute top-2 right-2 bg-surface/90 backdrop-blur-sm text-text-main text-xs font-bold px-2 py-1 rounded shadow-sm">
                    {property.rooms} {t('rooms')}
                </div>
            </div>

            {/* Content Area */}
            <div className="p-4 flex flex-col flex-grow">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-bold text-text-main line-clamp-2 leading-tight" title={property.title}>
                        {property.title}
                    </h3>
                </div>

                <p className="text-primary text-xl font-bold mb-3">
                    {formattedPrice}
                </p>

                <div className="flex items-center justify-between text-sm text-text-muted mt-auto mb-4 border-t border-border pt-3">
                    <div className="flex items-center gap-1">
                         <span>{property.area ? `${property.area} м²` : '-'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <span>{property.floor ? `${property.floor} ${t('floor')}` : '-'}</span>
                    </div>
                    <div className="text-xs px-2 py-0.5 bg-background rounded border border-border">
                        {property.city || 'N/A'}
                    </div>
                </div>

                <a
                    href={property.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-auto w-full block text-center py-2 px-4 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-colors text-sm font-medium"
                >
                    {t('more_details')}
                </a>
            </div>
        </div>
    );
};

export default PropertyCard;