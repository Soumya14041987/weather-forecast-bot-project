const LAMBDA_URL = 'https://yy4orcfzkddj3y64khcc2bm4v40login.lambda-url.us-east-1.on.aws/';

const weatherIcons = {
    'sunny': '☀️',
    'clear': '☀️',
    'partly-cloudy': '⛅',
    'cloudy': '☁️',
    'rainy': '🌧️',
    'stormy': '⛈️',
    'snowy': '❄️',
    'default': '🌤️'
};

const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function getWeatherIcon(condition) {
    return weatherIcons[condition] || weatherIcons.default;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
        return 'Tomorrow';
    } else {
        return `${dayNames[date.getDay()]}, ${monthNames[date.getMonth()]} ${date.getDate()}`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const cityInput = document.getElementById('cityInput');
    const loading = document.getElementById('loading');
    const weatherContent = document.getElementById('weatherContent');
    
    let searchTimeout;
    
    cityInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const city = cityInput.value.trim();
        
        if (city.length >= 3) {
            searchTimeout = setTimeout(() => {
                fetchWeather(city);
            }, 800);
        }
    });
    
    cityInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const city = cityInput.value.trim();
            if (city) {
                fetchWeather(city);
            }
        }
    });
    
    async function fetchWeather(city) {
        loading.classList.remove('hidden');
        weatherContent.classList.add('hidden');
        weatherContent.innerHTML = '';
        
        try {
            const response = await fetch(LAMBDA_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ city })
            });
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
            } else {
                displayWeather(data);
            }
        } catch (error) {
            showError('Unable to fetch weather data. Please try again.');
        } finally {
            loading.classList.add('hidden');
        }
    }
    
    function displayWeather(data) {
        const icon = getWeatherIcon(data.current_condition);
        const location = data.location;
        const current = data.current;
        
        // Calculate current temp (use actual temp or average of max/min)
        const currentTemp = current.temp !== undefined && !isNaN(current.temp) ? current.temp : 
                           Math.round((current.temp_max + current.temp_min) / 2);
        
        // Calculate feels like with proper fallback
        let feelsLike;
        if (current.feels_like !== undefined && !isNaN(current.feels_like)) {
            feelsLike = current.feels_like;
        } else if (current.feels_like_max !== undefined && current.feels_like_min !== undefined) {
            feelsLike = (current.feels_like_max + current.feels_like_min) / 2;
        } else {
            // If no feels like data, use actual temp
            feelsLike = currentTemp;
        }
        
        let html = `
            <div class="current-weather">
                <div class="location-name">${location.city}</div>
                <div class="weather-icon-large">${icon}</div>
                <div class="current-temp">${currentTemp.toFixed(1)}°</div>
                <div class="temp-range">Feels like ${feelsLike.toFixed(1)}° • H: ${current.temp_max.toFixed(1)}° L: ${current.temp_min.toFixed(1)}°</div>
                <div class="weather-summary">${data.summary}</div>
            </div>
        `;
        
        // Weather Alerts
        if (data.alerts && data.alerts.length > 0) {
            html += `
                <div class="alerts-section">
                    <div class="section-title">⚠️ Weather Alerts</div>
            `;
            
            data.alerts.forEach(alert => {
                html += `<div class="alert-item">${alert}</div>`;
            });
            
            html += `</div>`;
        }
        
        // Stats Grid
        if (data.forecast && data.forecast.length > 0) {
            const weekPrecip = data.forecast.slice(0, 7).reduce((sum, day) => sum + day.precipitation, 0);
            const weekMaxTemp = Math.max(...data.forecast.slice(0, 7).map(d => d.temp_max));
            const weekMinTemp = Math.min(...data.forecast.slice(0, 7).map(d => d.temp_min));
            
            html += `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Feels Like</div>
                        <div class="stat-value">${feelsLike.toFixed(1)}°</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Week High</div>
                        <div class="stat-value">${weekMaxTemp.toFixed(1)}°</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Week Low</div>
                        <div class="stat-value">${weekMinTemp.toFixed(1)}°</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Precipitation</div>
                        <div class="stat-value">${weekPrecip.toFixed(1)}mm</div>
                    </div>
                </div>
            `;
        }
        
        // Insights
        if (data.insights && data.insights.length > 0) {
            html += `
                <div class="insights-section">
                    <div class="section-title">Weather Insights</div>
            `;
            
            data.insights.forEach(insight => {
                html += `<div class="insight-item">${insight}</div>`;
            });
            
            html += `</div>`;
        }
        
        // Recommendation
        if (data.recommendation) {
            html += `
                <div class="recommendation-card">
                    <div class="recommendation-icon">💡</div>
                    <div class="recommendation-text">${data.recommendation}</div>
                </div>
            `;
        }
        
        // 10-Day Forecast
        if (data.forecast && data.forecast.length > 0) {
            html += `
                <div class="forecast-section">
                    <div class="section-title">10-Day Forecast</div>
                    <div class="forecast-list">
            `;
            
            data.forecast.forEach((day, index) => {
                let dayIcon = icon;
                
                // Determine icon based on conditions
                if (day.snowfall > 5) {
                    dayIcon = '❄️';
                } else if (day.snowfall > 0) {
                    dayIcon = '🌨️';
                } else if (day.rain > 10) {
                    dayIcon = '🌧️';
                } else if (day.rain > 0 || day.precipitation > 5) {
                    dayIcon = '🌦️';
                } else if (day.precipitation_prob > 60) {
                    dayIcon = '☁️';
                }
                
                // Show additional info for days with significant weather
                let extraInfo = '';
                if (day.precipitation > 0) {
                    extraInfo = `<div class="forecast-extra">💧 ${day.precipitation.toFixed(1)}mm`;
                    if (day.precipitation_prob > 0) {
                        extraInfo += ` (${day.precipitation_prob}%)`;
                    }
                    extraInfo += `</div>`;
                }
                if (day.snowfall > 0) {
                    extraInfo += `<div class="forecast-extra">❄️ ${day.snowfall.toFixed(1)}mm snow</div>`;
                }
                
                html += `
                    <div class="forecast-day">
                        <div class="forecast-info">
                            <div class="forecast-date">${formatDate(day.date)}</div>
                            ${extraInfo}
                        </div>
                        <div class="forecast-icon">${dayIcon}</div>
                        <div class="forecast-temps">
                            <span class="temp-max">${day.temp_max.toFixed(1)}°</span>
                            <span class="temp-min">${day.temp_min.toFixed(1)}°</span>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        weatherContent.innerHTML = html;
        weatherContent.classList.remove('hidden');
    }
    
    function showError(message) {
        weatherContent.innerHTML = `
            <div class="error-card">
                <div class="error-icon">⚠️</div>
                <div class="error-message">${message}</div>
            </div>
        `;
        weatherContent.classList.remove('hidden');
    }
});
