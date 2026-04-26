import { useState, useEffect } from 'react';
import { getGeography } from '../api/client';
import { Globe, MapPin, Flag, Activity } from 'lucide-react';

export default function GeoAttackMap() {
  const [geoData, setGeoData] = useState(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(null);

  useEffect(() => {
    loadGeoData();
  }, [days]);

  const loadGeoData = async () => {
    setLoading(true);
    try {
      const data = await getGeography(days);
      setGeoData(data);
    } catch (err) {
      console.error('Failed to load geography data:', err);
    } finally {
      setLoading(false);
    }
  };

  const maxAttacks = geoData?.countries?.length > 0 
    ? Math.max(...geoData.countries.map(c => c.attacks))
    : 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
          <Globe className="w-4 h-4" />
          Geographic Attack Distribution
        </h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-netbg border border-netborder text-[#e6edf3] font-mono text-xs rounded px-2 py-1"
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      {loading && (
        <div className="text-center py-8 text-netcyan font-mono text-sm animate-pulse">
          Loading geographic data...
        </div>
      )}

      {!loading && !geoData && (
        <div className="text-center py-12 text-[#8b9ab3] font-mono">
          <Globe className="w-12 h-12 mx-auto mb-4 text-netborder" />
          <p className="text-lg">No data available</p>
          <p className="text-sm">Start capturing traffic to see geographic distribution</p>
        </div>
      )}

      {!loading && geoData && !geoData.countries?.length && !geoData.cities?.length && !geoData.map_points?.length && (
        <div className="text-center py-12 text-[#8b9ab3] font-mono">
          <Globe className="w-12 h-12 mx-auto mb-4 text-netborder" />
          <p className="text-lg mb-2">No geographic data available</p>
          <p className="text-sm text-netcyan">Start capturing traffic to see attack origins</p>
        </div>
      )}

      {!loading && geoData && (
        <>
          {/* Stats Summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="border border-netborder bg-netsurface rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Countries</p>
              <p className="text-2xl font-mono text-netcyan">{geoData.countries?.length || 0}</p>
            </div>
            <div className="border border-netborder bg-netsurface rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Cities</p>
              <p className="text-2xl font-mono text-netorange">{geoData.cities?.length || 0}</p>
            </div>
            <div className="border border-netborder bg-netsurface rounded p-3 text-center">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Map Points</p>
              <p className="text-2xl font-mono text-netred">{geoData.map_points?.length || 0}</p>
            </div>
          </div>

          {/* Country List */}
          <div className="border border-netborder bg-netsurface rounded p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
              <Flag className="w-3 h-3" />
              Top Attacking Countries
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {geoData.countries?.slice(0, 15).map((country, i) => {
                const intensity = maxAttacks > 0 ? (country.attacks / maxAttacks) : 0;
                return (
                  <div
                    key={country.name}
                    className="flex items-center gap-3 p-2 rounded hover:bg-netbg cursor-pointer transition-colors"
                    onClick={() => setSelectedCountry(country.name)}
                  >
                    <span className="text-xs font-mono text-[#5a6a7a] w-6">#{i + 1}</span>
                    <span className="text-sm font-mono text-[#e6edf3] flex-1">
                      {country.name || 'Unknown'}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-netbg rounded overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-netcyan to-netred"
                          style={{ width: `${intensity * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-netred w-12 text-right">
                        {country.attacks}
                      </span>
                    </div>
                  </div>
                );
              })}
              {(!geoData.countries || geoData.countries.length === 0) && (
                <p className="text-xs font-mono text-[#5a6a7a] text-center py-4">
                  No geographic data available
                </p>
              )}
            </div>
          </div>

          {/* Cities List */}
          <div className="border border-netborder bg-netsurface rounded p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
              <MapPin className="w-3 h-3" />
              Top Attacking Cities
            </h3>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {geoData.cities?.slice(0, 20).map((city, i) => (
                <div
                  key={`${city.name}-${i}`}
                  className="flex items-center justify-between p-2 rounded bg-netbg"
                >
                  <span className="text-xs font-mono text-[#e6edf3] truncate">
                    {city.name}, {city.country}
                  </span>
                  <span className="text-xs font-mono text-netorange">{city.attacks}</span>
                </div>
              ))}
              {(!geoData.cities || geoData.cities.length === 0) && (
                <p className="text-xs font-mono text-[#5a6a7a] text-center py-4 col-span-2">
                  No city data available
                </p>
              )}
            </div>
          </div>

          {/* Map Points Visualization */}
          {geoData.map_points && geoData.map_points.length > 0 && (
            <div className="border border-netborder bg-netsurface rounded p-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3">
                Attack Coordinates ({geoData.map_points.length} points)
              </h3>
              <div className="max-h-48 overflow-y-auto space-y-1">
                {geoData.map_points.slice(0, 50).map((point, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs font-mono">
                    <span className="text-netred">●</span>
                    <span className="text-[#8b9ab3]">{point.ip}</span>
                    <span className="text-[#5a6a7a]">
                      ({point.lat?.toFixed(2)}, {point.lon?.toFixed(2)})
                    </span>
                    <span className="text-netcyan truncate">{point.city}, {point.country}</span>
                  </div>
                ))}
                {geoData.map_points.length > 50 && (
                  <p className="text-xs font-mono text-[#5a6a7a] text-center py-2">
                    +{geoData.map_points.length - 50} more points...
                  </p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
