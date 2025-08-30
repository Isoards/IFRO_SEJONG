import React from "react";
import GoogleMapWrapper from "./GoogleMapWrapper";

interface SejongHeatmapProps {
    className?: string;
}

const SejongHeatmap: React.FC<SejongHeatmapProps> = ({ className = "" }) => {
    // 세종시 중심 좌표
    const sejongCenter = { lat: 36.5040736, lng: 127.2494855 };

    return (
        <div className={className}>
            <GoogleMapWrapper
                selectedIntersection={null}
                onIntersectionClick={() => { }}
                intersections={[]}
                center={sejongCenter}
            />
        </div>
    );
};

export default SejongHeatmap;