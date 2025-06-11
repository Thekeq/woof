setInterval(() => {
    if (window.outerWidth - window.innerWidth > 100 || window.outerHeight - window.innerHeight > 100) {
        location.reload();
    }
}, 500);

const userId = window.userId
const inviteItemsData = {
    'limited': [],
    'in-game': [],
    'partners': []
};

// Динамическая загрузка заданий с сервера
async function loadTasks(activeTab = 'limited') {
    try {
        await update_balance(userId)
        inviteItemsData['limited'] = [];
        inviteItemsData['in-game'] = [];
        inviteItemsData['partners'] = [];

        const response = await fetch(`/api/tasks?userId=${userId}`);
        const tasks = await response.json();

        tasks.forEach(task => {
            if (inviteItemsData[task.type]) {
                inviteItemsData[task.type].push(task);
            }
        });

        // Обновление количества заданий в каждой вкладке
        updateTaskCount('in-game');
        updateTaskCount('limited');
        updateTaskCount('partners');

        showQuest(`${activeTab}`)
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

async function loadFrens(userId) {
    const data = await user_info(userId);  // Получаем данные пользователя

    const frensList = data['frens_list'].split(',');  // Преобразуем строку в массив
    const frensTime = data['frens_time'].split(',');  // Преобразуем строку в массив
    const frensRewards = data['frens_rewards']; // Получаем награды друзей
    const frensCount = data['frens_count'];

    const countElement = document.querySelector(`#frens .count`);
    countElement.textContent = `${frensCount.toString()} users`;

    const frensContainer = document.getElementById('frens-container');
    if (!frensContainer) {
        return; // Если контейнер не найден, завершаем выполнение
    }

    frensContainer.innerHTML = '';  // Очищаем контейнер перед добавлением новых элементов

    // Проверяем, что массивы не пусты
    if (frensList.length === 0 || frensTime.length === 0) {
        return;
    }

    // Делаем проверку, чтобы данные корректно отображались
    if (frensList.length === frensTime.length && frensList.length === frensCount) {
        frensList.forEach((frens, index) => {
            const inviteItem = document.createElement('div');
            inviteItem.classList.add('invite-item');

            // Преобразование времени из Unix timestamp в читаемый формат
            const timestamp = Math.floor(parseFloat(frensTime[index])); // Убираем дробную часть и получаем целые секунды
            const date = new Date(timestamp * 1000); // Переводим в миллисекунды для Date

            const options = {
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            const formattedDate = date.toLocaleString('en-US', options); // Форматируем дату

            const frenId = data['frens_id'].split(',')[index];
            const rewards = frensRewards[frenId];
            let frenReward = 0;
            if (rewards && rewards['Age']) {
                frenReward = rewards['Age'];
            }
            const userShare = Math.round(frenReward * 0.15); // 15% награды друга

            const taskContent = `
                <div class="main-info">
                    <div class="icon-con">
                        <img alt="" loading="lazy" width="18" height="18" decoding="async" data-nimg="1" src="/static/media/invite.svg" style="color: transparent;">
                    </div>
                    <div class="wallet-con">
                        <div class="wallet">${frens}</div> <!-- Имя друга -->
                        <div class="date">${formattedDate}</div> <!-- Время -->
                    </div>
                </div>
                <div class="points">
                    <p class="amount">${userShare} WOOFS</p>
                    <p class="descr">Received</p>
                </div>
            `;

            inviteItem.innerHTML = taskContent;
            frensContainer.appendChild(inviteItem);
        });
    } else {
        console.error("Data mismatch: frens_list, frens_time, and frens_count must have the same length.");
    }
}


async function loadLeaderboard(page = 0, limit = 100, userId = null) {
    try {
        const response = await fetch(`/api/leaderboard?page=${page}&limit=${limit}&userId=${userId}`);
        const data = await response.json();

        if (data.success) {
            const leaderboard = data.data.list;
            const leaderboardUser = data.data.userData;
            const userPosition = data.data.userData.position; // Позиция текущего пользователя
            const user = leaderboardUser.find((user) => user.rank === userPosition); // Находим текущего пользователя
            const leaderboardContainer = document.getElementById('leaders-list');
            const totalUsersElement = document.querySelector('#leaders .total-users .count');
            const userItemCon = document.querySelector('.user-item-con');

            // Обновляем общее количество пользователей
            totalUsersElement.textContent = `${data.data.count.toLocaleString()} users`;

            // Очищаем контейнер перед добавлением новых данных
            leaderboardContainer.innerHTML = '';
            // Обновляем данные текущего пользователя в `user-item-con`
            if (userItemCon && user) {
                userItemCon.querySelector('.wallet').textContent = user.username || 'Anonymous';
                userItemCon.querySelector('.balance').textContent = `${user.balance.toLocaleString()} WOOFS`;
                userItemCon.querySelector('.place').textContent = `#${user.position}`;
            }
            // Генерация списка лидеров
            leaderboard.forEach((user) => {
                const leaderElement = document.createElement('div');
                leaderElement.className = 'leader-icon-con';
                leaderElement.innerHTML = `
                    <div class="side-info">
                        <div class="img-con">
                            <img alt="" loading="lazy" width="25" height="25" decoding="async" src="/static/media/woofsLogoBlack.svg" style="color: transparent;">
                        </div>
                        <div class="main-info-con">
                            <div class="wallet">${user.username || 'Anonymous'}</div>
                            <div class="balance">${user.balance.toLocaleString()} WOOFS</div>
                        </div>
                    </div>
                    <div class="place">#${user.rank}</div>
                `;
                leaderboardContainer.appendChild(leaderElement);
            });
        } else {
            console.error(data.error);
        }
    } catch (error) {
        console.error("Error loading leaderboard:", error);
    }
}

async function loadRewards(userId) {
    try {
        const response = await fetch(`/api/rewards?userId=${userId}`);
        const data = await response.json();

        if (data.success) {
            const rewardsContainer = document.querySelector('.section-items-con.transactions');
            rewardsContainer.innerHTML = ''; // Очистить текущий список

            data.data.forEach(reward => {
                const rewardItem = document.createElement('div');
                if (reward.title === 'Age') {
                    reward.title = 'Telegram Age';
                    reward.src = "/static/media/telegram.svg"
                }
                if (reward.title === 'checkin') {
                    reward.title = 'Daily Check-In';
                    reward.src = "/static/media/check.svg"
                    reward.amount *= 100
                }
                if (reward.title === 'Welcome') {
                    reward.title = 'Welcome bonus!';
                    reward.src = "/static/media/wooflogo.svg"
                }
                if (reward.title === 'premium') {
                    reward.title = 'Telegram Premium!';
                    reward.src = "/static/media/premium.svg"
                }
                if (reward.title === 'subTG') {
                    reward.title = 'Follow channel';
                    reward.src = "/static/media/telegram.svg"
                }
                if (reward.title === 'partner') {
                    reward.title = 'Follow partner';
                    reward.src = "/static/media/telegram.svg"
                }
                if (reward.title === 'invite') {
                    reward.title = 'Task completed';
                    reward.src = "/static/media/invitefren.svg"
                }
                if (reward.title === 'newyear') {
                    reward.title = 'Happy New Year!';
                    reward.src = "https://em-content.zobj.net/source/telegram/361/christmas-tree_1f384.webp"
                }
                if (reward.title === 'Complete Task (Frens)') {
                    reward.title = 'Task completed';
                    reward.src = "/static/media/invitefren.svg"
                }
                if (reward.title === 'Boost') {
                    reward.title = 'Boost Channel';
                    reward.src = "/static/media/boost.png"
                }
                rewardItem.className = 'invite-item';
                rewardItem.innerHTML = `
                    <div class="main-info">
                        <div class="icon-con">
                            <img alt="" loading="lazy" width="40" height="40" decoding="async" src=${reward.src} style="color: transparent;">
                        </div>
                        <div class="wallet-con">
                            <div class="wallet">${reward.title}</div>
                            <div class="date">Your reward <3</div>
                        </div>
                    </div>
                    <div class="points">
                        <p>+${reward.amount.toLocaleString()} WOOFS</p>
                        <p class="descr">Received</p>
                    </div>
                `;
                rewardsContainer.appendChild(rewardItem);
            });

            // Добавляем кнопку "Show more"
            const showMoreBtn = document.createElement('div');
            showMoreBtn.className = 'show-more';
            showMoreBtn.textContent = 'Show more';
            //rewardsContainer.appendChild(showMoreBtn);
        } else {
            console.error("Failed to fetch rewards:", data.error);
        }
    } catch (error) {
        console.error("Error loading rewards:", error);
    }
}

function updateTaskCount(tabId, elementId) {
    const tabs = ['limited', 'in-game', 'partners'];
    tabs.forEach(tab => {
        showQuest(`${tab}`);
        const startButtons = document.querySelectorAll(`.invite-item .start-btn`);
        const taskCount = startButtons.length;
        const countElement = document.querySelector(`#${tab} .count`);

        if (countElement) {
            if (taskCount === 0) {
                countElement.style.display = 'none'; // Скрыть элемент, если заданий нет
            } else {
                countElement.textContent = taskCount.toString();
            }
        }
    })

    showQuest(`${elementId}`);
}


function showTab(tabId) {
    // Убираем активность у всех вкладок
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.style.display = 'none';
    });

    // Убираем активный класс у всех ссылок
    const tabItems = document.querySelectorAll('.tab-content');
    tabItems.forEach(item => {
        item.classList.remove('active');
    });

    // Убираем активный класс у всех ссылок
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    // Показываем активную вкладку
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.style.display = 'flex';
    }

    // Добавляем активный класс к текущей вкладке
    const activeTabItem = document.getElementById(tabId);
    if (activeTabItem) {
        activeTabItem.classList.add('active');
    }
    // Добавляем активный класс к текущей вкладке
    const activeNavItem = document.querySelector(`.nav-item[onclick="showTab('${tabId}')"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
}

function showRewards(tabId) {
    // Показываем активную вкладку
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.style.display = 'flex';
    }

    // Добавляем активный класс к текущей вкладке
    const activeNavItem = document.getElementById(tabId);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
}


function showQuest(tabId) {
    // Убираем активный класс у всех ссылок
    const navItems = document.querySelectorAll('.type-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    // Добавляем активный класс к текущей вкладке
    const activeNavItem = document.getElementById(tabId);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    // Получаем контейнер для invite-items
    const questsContainer = document.getElementById('quests-container');

    // Очищаем контейнер перед добавлением новых элементов
    questsContainer.innerHTML = '';

    // Добавляем соответствующие invite-items в контейнер
    const items = inviteItemsData[tabId] || [];
    items.forEach(itemData => {
        const inviteItem = document.createElement('div');
        inviteItem.classList.add('invite-item');

        // Если задание имеет remaining_time, добавляем обратный отсчет
        let taskContent = `
            <div class="main-info">
                <div class="icon-con">
                    <img alt="" loading="lazy" width="40" height="40" decoding="async" src="${itemData.icon}" style="color: transparent;">
                </div>
                <div class="wallet-con">
                    <div class="wallet">${itemData.description}</div>
                    <p class="reward-count">${itemData.reward}</p>
                </div>
            </div>`;

        if (itemData.id === 3) {
            if (itemData.completed) {
                taskContent += `
                    <div class="points" id="task-${itemData.id}">
                        <div class="check-con">
                            <img alt="" loading="lazy" width="16" height="14" decoding="async" data-nimg="1" src="/static/media/done.svg" style="color: transparent;">
                        </div>
                    </div>
                `;
            } else {
                taskContent += `
                        <div class="points" id="task-${itemData.id}">
                            <div class="start-btn" onclick="${itemData.onclick}">Check</div>
                        </div>
                    `;
            }
        } else if (itemData.id === 4) {
            if (itemData.completed) {
                taskContent += `
                    <div class="points" id="task-${itemData.id}">
                        <div class="check-con">
                            <img alt="" loading="lazy" width="16" height="14" decoding="async" data-nimg="1" src="/static/media/done.svg" style="color: transparent;">
                        </div>
                    </div>
                `;
            } else {
                taskContent += `
                        <div class="points" id="task-${itemData.id}">
                            <div class="start-btn" onclick="${itemData.onclick}">Start</div>
                        </div>
                    `;
            }
        }
        // Если задание с обратным отсчетом
        else if (itemData.remaining_time > 0) {
            taskContent += `
                <div class="points" id="task-${itemData.id}">
                    <div class="cooldown">Available in ${formatTime(itemData.remaining_time)}</div>
                </div>
            `;
            startCountdown(itemData.id, Math.ceil(itemData.remaining_time));

        } else {
            // Сначала проверяем, завершено ли задание
            if (itemData.completed) {
                taskContent += `
                    <div class="points" id="task-${itemData.id}">
                        <div class="check-con">
                            <img alt="" loading="lazy" width="16" height="14" decoding="async" data-nimg="1" src="/static/media/done.svg" style="color: transparent;">
                        </div>
                    </div>
                `;
            } else {
                // Если задание доступно и не завершено, проверяем для id === 2
                if (itemData.id === 2) {
                    taskContent += `
                        <div class="points" id="task-${itemData.id}">
                            <div class="start-btn" onclick="${itemData.onclick}">Start</div>
                            <div class="loading-animation" style="display: none;">Sending transaction...</div>
                        </div>
                    `;
                } else {
                    // Для остальных заданий
                    taskContent += `
                        <div class="points">
                            <div class="start-btn" onclick="${itemData.onclick}">Start</div>
                        </div>
                    `;
                }
            }
        }

        inviteItem.innerHTML = taskContent;
        questsContainer.appendChild(inviteItem);
    });
}


// Функция для форматирования времени
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}:${minutes.toString().padStart(2, '0')}`;
}

// Функция для обратного отсчета
// Хранение активных интервалов
const activeIntervals = {};

function startCountdown(taskId, remainingTime) {
    // Если для этой задачи таймер уже запущен, не запускаем его снова
    if (activeIntervals[taskId]) {
        return;
    }

    const interval = setInterval(() => {
        if (remainingTime <= 0) {
            clearInterval(interval);
            delete activeIntervals[taskId]; // Удаляем из активных интервалов

            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                taskElement.innerHTML = `<div class="start-btn" onclick="checkin(${userId})">Start</div>`;
                taskElement.innerHTML += `<div class="loading-animation" style="display: none;">Sending transaction...</div>`;
            }
            return;
        }

        // Обновляем время
        const taskElement = document.getElementById(`task-${taskId}`);
        if (taskElement) {
            taskElement.innerHTML = `<div class="cooldown">Available in ${formatTime(remainingTime)}</div>`;
        }

        remainingTime--;
    }, 1000);

    // Сохраняем интервал как активный
    activeIntervals[taskId] = interval;
}

async function subscribeToTelegram(userId) {
    window.TelegramWebApp.openTelegramLink("https://t.me/woofsupfam");

    try {
        const response = await fetch('/completeTask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userId: userId,
                task_id: 1,
                type: "subTG"
            })
        });

        // Убедимся, что запрос выполнен успешно
        if (!response.ok) {
        }

        const data = await response.json(); // Ждем и преобразуем в JSON

        if (data.status === 'success') {
            const activeElement = document.querySelector('.type-item.active');
            const elementId = activeElement.id;
            loadTasks(elementId); // Перезагружаем задачи, если все ок
        } else {
            console.error('Task completion failed:', data.message);
        }
    } catch (error) {
        console.error('Error completing task:', error);
    }
}

async function partnerTelegram(userId, link, id) {
    window.TelegramWebApp.openTelegramLink(link);

    try {
        const response = await fetch('/completeTask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userId: userId,
                task_id: id,
                type: "partner"
            })
        });

        // Убедимся, что запрос выполнен успешно
        if (!response.ok) {
        }

        const data = await response.json(); // Ждем и преобразуем в JSON

        if (data.status === 'success') {
            const activeElement = document.querySelector('.type-item.active');
            const elementId = activeElement.id;
            loadTasks(elementId); // Перезагружаем задачи, если все ок
        } else {
            console.error('Task completion failed:', data.message);
        }
    } catch (error) {
        console.error('Error completing task:', error);
    }
}

async function boostChannel(userId, link, id) {
    window.TelegramWebApp.openTelegramLink(link);

    // Проверка статуса через сервер
    try {
        const response = await fetch('/checkMembership', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: userId, channel: 'boost/woofsupfam' })
        });

        const data = await response.json();

        if (data.status === 'success' && data.isMember) {
            // Пользователь подписан или сделал буст
            await fetch('/completeTask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: userId,
                    task_id: id,
                    type: "Boost"
                })
            });
            window.TelegramWebApp.showAlert("Task completed successfully!");
        } else {
            window.TelegramWebApp.showAlert("You need to join or boost the channel first!");
        }
    } catch (error) {
        window.TelegramWebApp.showAlert("An error occurred while processing your task. Please try again.");
        console.error('Error:', error);
    }
}


async function user_friends(userId) {
    const data = await user_info(userId);
    const frensCount = data['frens_count'];
    if (frensCount >= 10) {
        try {
            const response = await fetch('/completeTask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    userId: userId,
                    task_id: 3,
                    type: "invite"
                })
            });

            // Убедимся, что запрос выполнен успешно
            if (!response.ok) {
            }

            const data = await response.json(); // Ждем и преобразуем в JSON

            if (data.status === 'success') {
                const activeElement = document.querySelector('.type-item.active');
                const elementId = activeElement.id;
                loadTasks(elementId); // Перезагружаем задачи, если все ок
                loadRewards(userId);
            } else {
                console.error('Task completion failed:', data.message);
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    } else {
        invite(userId)
    }
}

async function invite_fren_limit(userId, amount, taskid) {
    const data = await user_info(userId);
    const frensCount = data['frens_count'];
    if (frensCount >= amount) {
        try {
            const response = await fetch('/completeTask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    userId: userId,
                    task_id: taskid,
                    type: "Complete Task (Frens)"
                })
            });

            // Убедимся, что запрос выполнен успешно
            if (!response.ok) {
            }

            const data = await response.json(); // Ждем и преобразуем в JSON

            if (data.status === 'success') {
                const activeElement = document.querySelector('.type-item.active');
                const elementId = activeElement.id;
                loadTasks(elementId); // Перезагружаем задачи, если все ок
                loadRewards(userId);
            } else {
                console.error('Task completion failed:', data.message);
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    } else {
        invite(userId)
    }
}

async function user_premium(userId) {

    if (premium === true) {
        try {
            const response = await fetch('/completeTask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    userId: userId,
                    task_id: 3,
                    type: "premium"
                })
            });

            // Убедимся, что запрос выполнен успешно
            if (!response.ok) {
            }

            const data = await response.json(); // Ждем и преобразуем в JSON

            if (data.status === 'success') {
                const activeElement = document.querySelector('.type-item.active');
                const elementId = activeElement.id;
                loadTasks(elementId); // Перезагружаем задачи, если все ок
                loadRewards(userId);
            } else {
                console.error('Task completion failed:', data.message);
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    }
}

async function user_info(userId) {
    try {
        const response = await fetch(`/userInfo?userId=${userId}`);

        // Убедимся, что запрос выполнен успешно
        if (!response.ok) {
        }


        // Ждем и преобразуем в JSON
        return await response.json()

    } catch (error) {
        console.error('Error update balance');
    }
}

async function update_balance(userId) {
    let user_data;
    try {
        user_data = await user_info(userId)
        balance = user_data['balance']
        console.log(user_data)
        const count = document.querySelector('#home .count');
        if (count) {
            count.textContent = balance;
        }

    } catch (error) {
        console.error('Error update balance');
    }
}

function invite(userId) {
    const message = `https://t.me/WOOFSOG_bot?start=${userId}`;
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(message)}`;
    window.TelegramWebApp.openTelegramLink(telegramUrl);
}

// Инициализация с вкладки по умолчанию
document.addEventListener('DOMContentLoaded', () => {
    showQuest('limited'); // или 'in-game' / 'partners' в зависимости от дефолтной вкладки
    showTab('home');
    loadTasks();
    loadFrens(userId);
    loadLeaderboard(0, 100, userId);
});

window.onload = function () {
    const loadingScreen = document.getElementById('loading-screen');
    // Убираем анимацию загрузки, когда все ресурсы загружены
    loadingScreen.style.display = 'none';
};

