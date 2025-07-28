// Analytics Dashboard JavaScript

class AnalyticsDashboard {
    constructor() {
        this.chart = null;
        this.colors = {
            low: '#10b981',
            medium: '#f59e0b', 
            high: '#ef4444'
        };
    }

    async fetchAnalyticsData(city, date) {
        try {
            const response = await fetch(`/analytics/${city}/${date}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            return data;
        } catch (error) {
            console.error('Error fetching analytics:', error);
            throw error;
        }
    }

    updateSummaryCards(summary) {
        document.getElementById('total-towns').textContent = summary.total_towns;
        document.getElementById('avg-probability').textContent = `${summary.average_flood_probability}%`;
        document.getElementById('total-population').textContent = summary.total_population_affected.toLocaleString();
        document.getElementById('total-area').textContent = `${summary.total_area_at_risk} km²`;
    }

    updateRiskChart(riskDistribution, riskPercentages) {
        const canvas = document.getElementById('risk-chart');
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Create donut chart
        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    data: [
                        riskDistribution.low,
                        riskDistribution.medium,
                        riskDistribution.high
                    ],
                    backgroundColor: [
                        this.colors.low,
                        this.colors.medium,
                        this.colors.high
                    ],
                    borderWidth: 2,
                    borderColor: getComputedStyle(document.documentElement)
                        .getPropertyValue('--bg-secondary').trim(),
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} towns (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });

        // Update legend percentages
        document.getElementById('low-percentage').textContent = `${riskPercentages.low}%`;
        document.getElementById('medium-percentage').textContent = `${riskPercentages.medium}%`;
        document.getElementById('high-percentage').textContent = `${riskPercentages.high}%`;
    }

    updateTopTowns(topTowns) {
        const container = document.getElementById('top-towns-list');
        container.innerHTML = '';

        topTowns.forEach((town, index) => {
            const riskLevel = this.getRiskLevel(town.probability / 100);
            
            const townElement = document.createElement('div');
            townElement.className = 'town-item';
            townElement.style.animationDelay = `${index * 0.1}s`;
            
            townElement.innerHTML = `
                <div class="town-header">
                    <div class="town-name">${town.town}</div>
                    <div class="town-risk ${riskLevel}">${town.probability}%</div>
                </div>
                <div class="town-details">
                    <div><i class="fas fa-users"></i> ${town.population_affected.toLocaleString()} people</div>
                    <div><i class="fas fa-expand"></i> ${town.size_covered} km²</div>
                </div>
            `;
            
            container.appendChild(townElement);
        });
    }

    getRiskLevel(probability) {
        if (probability < 0.3) return 'low';
        if (probability < 0.6) return 'medium';
        return 'high';
    }

    async loadAnalytics(city, date) {
        try {
            const data = await this.fetchAnalyticsData(city, date);
            
            // Show analytics dashboard
            const dashboard = document.getElementById('analytics-dashboard');
            dashboard.style.display = 'block';
            
            // Update all components
            this.updateSummaryCards(data.summary);
            this.updateRiskChart(data.risk_distribution, data.risk_percentages);
            this.updateTopTowns(data.top_risk_towns);
            
            // Add fade-in animation
            dashboard.style.opacity = '0';
            setTimeout(() => {
                dashboard.style.transition = 'opacity 0.5s ease';
                dashboard.style.opacity = '1';
            }, 100);
            
        } catch (error) {
            console.error('Failed to load analytics:', error);
            document.getElementById('analytics-dashboard').style.display = 'none';
        }
    }

    hideAnalytics() {
        document.getElementById('analytics-dashboard').style.display = 'none';
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Initialize analytics dashboard
window.analyticsDashboard = new AnalyticsDashboard();