/**
 * Социальные функции: комментарии, уведомления, таблица лидеров
 */

// Загрузка таблицы лидеров
async function loadLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard?limit=10');
        const data = await response.json();
        
        const container = document.getElementById('leaderboard-container');
        if (!container || !data.leaderboard) return;
        
        container.innerHTML = `
            <h3 class="text-xl font-bold mb-4 text-gray-800">🏆 Таблица лидеров</h3>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Уровень</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">XP</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Тесты</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${data.leaderboard.map((entry, index) => `
                            <tr class="${index < 3 ? 'bg-yellow-50' : ''}">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="text-lg font-bold ${index === 0 ? 'text-yellow-600' : index === 1 ? 'text-gray-600' : index === 2 ? 'text-orange-600' : 'text-gray-400'}">
                                        ${entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">${entry.username}</td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-primary-100 text-primary-800">
                                        Lvl ${entry.level}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-gray-600">${entry.experience}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-gray-600">${entry.quizzes_passed}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки таблицы лидеров:', error);
    }
}

// Загрузка комментариев для темы
async function loadComments(topicId) {
    try {
        const response = await fetch(`/api/comments/${topicId}`);
        const data = await response.json();
        
        const container = document.getElementById('comments-container');
        if (!container) return;
        
        if (!data.comments || data.comments.length === 0) {
            container.innerHTML = '<p class="text-gray-500 italic">Комментариев пока нет. Будьте первым!</p>';
            return;
        }
        
        container.innerHTML = `
            <h3 class="text-xl font-bold mb-4 text-gray-800">💬 Комментарии (${data.comments.length})</h3>
            <div class="space-y-4">
                ${data.comments.map(c => `
                    <div class="bg-white p-4 rounded-lg border border-gray-200">
                        <div class="flex items-start justify-between mb-2">
                            <div class="flex items-center space-x-2">
                                <span class="font-semibold text-gray-900">${c.username}</span>
                                <span class="text-xs text-gray-500">${new Date(c.created_at).toLocaleDateString()}</span>
                            </div>
                            <button onclick="likeComment('${c.id}')" class="flex items-center space-x-1 text-gray-500 hover:text-red-500 transition-colors">
                                <span>❤️</span>
                                <span class="text-sm">${c.likes}</span>
                            </button>
                        </div>
                        <p class="text-gray-700">${c.content}</p>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки комментариев:', error);
    }
}

// Добавление комментария
async function addComment(topicId, content) {
    try {
        const formData = new FormData();
        formData.append('topic_id', topicId);
        formData.append('content', content);
        
        const response = await fetch('/api/comments', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            // Обновить список комментариев
            loadComments(topicId);
            // Очистить форму
            document.getElementById('comment-content').value = '';
            return true;
        }
    } catch (error) {
        console.error('Ошибка добавления комментария:', error);
    }
    return false;
}

// Лайк комментария
async function likeComment(commentId) {
    try {
        const response = await fetch(`/api/comments/${commentId}/like`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Обновить отображение лайков
            const topicId = document.querySelector('[data-topic-id]')?.dataset.topicId;
            if (topicId) loadComments(parseInt(topicId));
        }
    } catch (error) {
        console.error('Ошибка лайка:', error);
    }
}

// Загрузка уведомлений
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();
        
        const badge = document.getElementById('notification-badge');
        const dropdown = document.getElementById('notification-dropdown');
        
        if (!data.notifications || data.notifications.length === 0) {
            if (badge) badge.classList.add('hidden');
            return;
        }
        
        // Показать бейдж с количеством
        if (badge) {
            badge.textContent = data.notifications.length;
            badge.classList.remove('hidden');
        }
        
        // Обновить выпадающий список
        if (dropdown) {
            dropdown.innerHTML = data.notifications.map(n => `
                <div class="p-3 border-b hover:bg-gray-50 cursor-pointer" onclick="markNotificationRead('${n.id}')">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h4 class="font-semibold text-sm text-gray-900">${n.title}</h4>
                            <p class="text-xs text-gray-600 mt-1">${n.message}</p>
                            <span class="text-xs text-gray-400 mt-2 block">${new Date(n.created_at).toLocaleString()}</span>
                        </div>
                        <span class="text-lg">${n.type === 'achievement' ? '🏆' : n.type === 'challenge' ? '⚡' : '📢'}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Ошибка загрузки уведомлений:', error);
    }
}

// Отметить уведомление как прочитанное
async function markNotificationRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        // Перезагрузить уведомления
        loadNotifications();
    } catch (error) {
        console.error('Ошибка отметки уведомления:', error);
    }
}

// Получение сертификата
async function getCertificate() {
    try {
        const response = await fetch('/api/certificate');
        
        if (response.ok) {
            const data = await response.json();
            showCertificateModal(data.certificate);
        } else if (response.status === 404) {
            alert('Сертификат недоступен. Пройдите минимум 5 тестов для получения сертификата.');
        }
    } catch (error) {
        console.error('Ошибка получения сертификата:', error);
    }
}

// Показать модальное окно сертификата
function showCertificateModal(certificate) {
    const modal = document.getElementById('certificate-modal');
    if (!modal) return;
    
    modal.innerHTML = `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-8 max-w-2xl w-full mx-4">
                <div class="text-center">
                    <h2 class="text-3xl font-bold text-primary-700 mb-4">🎉 Сертификат о прохождении</h2>
                    <div class="border-4 border-primary-500 rounded-lg p-6 bg-gradient-to-br from-primary-50 to-white">
                        <p class="text-xl text-gray-700 mb-2">Выдан пользователю</p>
                        <p class="text-2xl font-bold text-primary-800 mb-4">${certificate.username}</p>
                        <div class="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                            <div>
                                <span class="block font-semibold">Уровень:</span>
                                ${certificate.level}
                            </div>
                            <div>
                                <span class="block font-semibold">Тем пройдено:</span>
                                ${certificate.topics_completed}
                            </div>
                            <div>
                                <span class="block font-semibold">Тестов сдано:</span>
                                ${certificate.quizzes_passed}
                            </div>
                            <div>
                                <span class="block font-semibold">Средний балл:</span>
                                ${certificate.average_score}%
                            </div>
                        </div>
                        <p class="text-xs text-gray-500">Дата выдачи: ${new Date(certificate.issued_at).toLocaleDateString()}</p>
                    </div>
                    <div class="mt-6 flex justify-center space-x-4">
                        <a href="${certificate.certificate_url}" target="_blank" class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">
                            Скачать PDF
                        </a>
                        <button onclick="document.getElementById('certificate-modal').innerHTML=''" class="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">
                            Закрыть
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Экспорт прогресса в PDF
async function exportProgressPDF() {
    try {
        window.open('/stats/export/pdf', '_blank');
    } catch (error) {
        console.error('Ошибка экспорта:', error);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Загрузка таблицы лидеров на странице статистики
    if (document.getElementById('leaderboard-container')) {
        loadLeaderboard();
    }
    
    // Загрузка комментариев на странице темы
    const topicElement = document.querySelector('[data-topic-id]');
    if (topicElement && document.getElementById('comments-container')) {
        const topicId = parseInt(topicElement.dataset.topicId);
        loadComments(topicId);
        
        // Обработчик формы комментариев
        const form = document.getElementById('comment-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const content = document.getElementById('comment-content').value.trim();
                if (content) {
                    await addComment(topicId, content);
                }
            });
        }
    }
    
    // Загрузка уведомлений
    loadNotifications();
    
    // Обновление уведомлений каждые 60 секунд
    setInterval(loadNotifications, 60000);
});
