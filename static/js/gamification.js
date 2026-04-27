/**
 * Геймификация: уровни, достижения, ежедневные вызовы
 */

// Обновление отображения уровня пользователя
function updateUserLevel(level, experience, nextLevelXp) {
    const levelEl = document.getElementById('user-level');
    const xpEl = document.getElementById('user-xp');
    const xpBar = document.getElementById('xp-bar');
    
    if (levelEl) {
        levelEl.textContent = level;
    }
    
    if (xpEl) {
        xpEl.textContent = `${experience} / ${nextLevelXp} XP`;
    }
    
    if (xpBar) {
        const percentage = (experience / nextLevelXp) * 100;
        xpBar.style.width = `${percentage}%`;
    }
}

// Отображение уведомлений о достижениях
function showAchievementNotification(achievement) {
    const container = document.getElementById('achievements-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = 'achievement-notification animate-fade-in-up bg-gradient-to-r from-yellow-400 to-orange-500 text-white p-4 rounded-lg shadow-lg mb-3';
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <span class="text-3xl">${achievement.icon}</span>
            <div>
                <h4 class="font-bold">🏆 Достижение разблокировано!</h4>
                <p class="text-sm">${achievement.name}</p>
                <p class="text-xs opacity-80">${achievement.description}</p>
            </div>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Удалить через 5 секунд
    setTimeout(() => {
        notification.classList.add('opacity-0', 'transition-opacity', 'duration-500');
        setTimeout(() => notification.remove(), 500);
    }, 5000);
}

// Загрузка и отображение достижений
async function loadAchievements() {
    try {
        const response = await fetch('/api/achievements');
        const data = await response.json();
        
        const container = document.getElementById('achievements-list');
        if (!container || !data.achievements) return;
        
        container.innerHTML = data.achievements.map(a => `
            <div class="achievement-item p-3 rounded-lg border-2 ${a.unlocked ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-gray-50 opacity-60'}">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">${a.icon}</span>
                    <div class="flex-1">
                        <h4 class="font-semibold ${a.unlocked ? 'text-green-700' : 'text-gray-500'}">${a.name}</h4>
                        <p class="text-sm text-gray-600">${a.description}</p>
                    </div>
                    ${a.unlocked ? '<span class="text-green-500">✓</span>' : '<span class="text-gray-400">🔒</span>'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Ошибка загрузки достижений:', error);
    }
}

// Загрузка ежедневного вызова
async function loadDailyChallenge() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        const container = document.getElementById('daily-challenge');
        if (!container || !data.daily_challenge) return;
        
        const challenge = data.daily_challenge;
        container.innerHTML = `
            <div class="bg-gradient-to-r from-purple-500 to-indigo-600 text-white p-4 rounded-lg shadow-md">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-lg">⚡ ${challenge.title}</h3>
                        <p class="text-sm opacity-90">${challenge.description}</p>
                        <p class="text-xs mt-2">⏰ Истекает: ${new Date(challenge.expires_at).toLocaleTimeString()}</p>
                    </div>
                    <div class="text-right">
                        <span class="text-2xl font-bold">+${challenge.bonus_xp} XP</span>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки ежедневного вызова:', error);
    }
}

// Обновление статистики в реальном времени
async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.user_progress) {
            updateUserLevel(
                data.user_progress.level,
                data.user_progress.experience,
                data.user_progress.next_level_xp
            );
        }
        
        // Проверка новых достижений
        if (data.unlocked_achievements) {
            const stored = localStorage.getItem('unlocked_achievements') || '[]';
            const storedIds = JSON.parse(stored).map(a => a.id);
            
            data.unlocked_achievements.forEach(a => {
                if (!storedIds.includes(a.id)) {
                    showAchievementNotification(a);
                }
            });
            
            localStorage.setItem('unlocked_achievements', JSON.stringify(data.unlocked_achievements));
        }
    } catch (error) {
        console.error('Ошибка обновления статистики:', error);
    }
}

// Поиск с автодополнением
let searchTimeout;
async function performSearch(query) {
    if (query.length < 2) {
        document.getElementById('search-results').innerHTML = '';
        return;
    }
    
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            const container = document.getElementById('search-results');
            if (!container) return;
            
            if (data.total_results === 0) {
                container.innerHTML = '<div class="p-4 text-gray-500">Ничего не найдено</div>';
                return;
            }
            
            let html = '<div class="max-h-96 overflow-y-auto">';
            
            if (data.topics.length > 0) {
                html += '<div class="p-3 bg-gray-50 font-semibold">Темы:</div>';
                html += data.topics.map(t => `
                    <a href="/topic/${t.id}" class="block p-3 hover:bg-gray-50 border-b">
                        <h4 class="font-medium text-primary-700">${t.title}</h4>
                        <p class="text-sm text-gray-600 truncate">${t.snippet}</p>
                        <span class="text-xs text-gray-400">${t.category}</span>
                    </a>
                `).join('');
            }
            
            if (data.glossary_terms.length > 0) {
                html += '<div class="p-3 bg-gray-50 font-semibold mt-2">Глоссарий:</div>';
                html += data.glossary_terms.map(t => `
                    <div class="block p-3 hover:bg-gray-50 border-b">
                        <h4 class="font-medium text-primary-700">${t.term}</h4>
                        <p class="text-sm text-gray-600 truncate">${t.definition}</p>
                    </div>
                `).join('');
            }
            
            html += '</div>';
            container.innerHTML = html;
        } catch (error) {
            console.error('Ошибка поиска:', error);
        }
    }, 300);
}

// Рекомендации для главной страницы
async function loadRecommendations() {
    try {
        const response = await fetch('/api/recommendations?limit=3');
        const data = await response.json();
        
        const container = document.getElementById('recommendations');
        if (!container || !data.recommendations) return;
        
        container.innerHTML = `
            <h3 class="text-xl font-bold mb-4 text-gray-800">📚 Рекомендуем изучить дальше:</h3>
            <div class="grid md:grid-cols-3 gap-4">
                ${data.recommendations.map(r => `
                    <a href="/topic/${r.id}" class="card-hover block bg-white p-4 rounded-lg shadow-md border-l-4 border-primary-500 hover:shadow-lg transition-shadow">
                        <h4 class="font-semibold text-primary-700 mb-2">${r.title}</h4>
                        <p class="text-sm text-gray-600 line-clamp-2">${r.content.substring(0, 100)}...</p>
                        <span class="text-xs text-primary-500 mt-2 inline-block">${r.category_name}</span>
                    </a>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем достижения
    loadAchievements();
    
    // Загружаем ежедневный вызов
    loadDailyChallenge();
    
    // Загружаем рекомендации
    loadRecommendations();
    
    // Обновляем статистику каждые 30 секунд
    setInterval(refreshStats, 30000);
    
    // Обработчик поиска
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            performSearch(e.target.value);
        });
    }
});
