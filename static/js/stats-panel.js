function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

window.csrftoken = csrftoken;

if (!csrftoken) {
    console.error('CSRF токен не найден. Проверьте настройки Django.');
}

async function sendRequest(url, data) {
    if (!csrftoken) {
        console.error('CSRF токен отсутствует');
        alert('Ошибка безопасности: токен отсутствует');
        return null;
    }

    const allowedUrls = [
        '/get-post/',
        '/get-specific-post/',
        '/toggle-like/',
        '/toggle-dislike/',
        '/increment-views/',
        '/comments/',
        '/add_comment/'
    ];
    
    if (!allowedUrls.includes(url)) {
        console.error('Недопустимый URL:', url);
        return null;
    }

    try {
        const dataString = JSON.stringify(data);
        if (dataString.length > 10000) {
            console.error('Данные слишком большие');
            alert('Ошибка: данные слишком большие');
            return null;
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: dataString,
            credentials: 'same-origin'
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Неожиданный формат ответа');
        }

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Произошла ошибка на сервере');
        }
        
        return result;
    } catch (error) {
        console.error('Ошибка запроса:', error);
        
        if (error.message.includes('Failed to fetch') || error.message.includes('Network')) {
            alert('Ошибка сети. Проверьте соединение.');
        } else {
            alert('Произошла ошибка. Попробуйте позже.');
        }
        
        return null;
    }
}


function formatCount(count) {
    if (typeof count !== 'number' || isNaN(count) || count < 0) {
        return '0';
    }
    
    if (count >= 1000000) {
        return (count / 1000000).toFixed(1) + 'M';
    } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'k';
    }
    return count.toString();
}


function updateElement(selector, property, value) {
    const element = document.querySelector(selector);
    if (element) {
        if (property === 'textContent') {
            element.textContent = value;
        } else if (property === 'className') {
            element.className = value;
        } else if (property === 'style') {
            Object.assign(element.style, value);
        }
    }
}


async function toggleLike(button) {
    if (!button || !button.dataset) {
        console.error('Некорректная кнопка лайка');
        return;
    }

    const postId = parseInt(button.dataset.postId);
    

    if (!postId || postId < 1) {
        console.error('Некорректный ID поста');
        return;
    }

    if (button.disabled) {
        return;
    }
    
    button.disabled = true;
    
    try {
        const result = await sendRequest('/toggle-like/', {
            post_id: postId
        });
        
        if (result && result.success) {
            const icon = button.querySelector('.stat-icon');
            const count = button.querySelector('.stat-count');
            
            if (!icon || !count) {
                console.error('Не найдены элементы кнопки лайка');
                return;
            }
            
            if (result.is_liked) {
                icon.textContent = '💖';
                button.classList.add('active');
                button.style.background = 'rgba(34, 197, 94, 0.8)';
            } else {
                icon.textContent = '❤️';
                button.classList.remove('active');
                button.style.background = 'rgba(0, 0, 0, 0.7)';
            }
            
            count.textContent = formatCount(result.likes);
            
            const dislikeButton = document.querySelector('.stat-item.dislike');
            if (dislikeButton) {
                const dislikeIcon = dislikeButton.querySelector('.stat-icon');
                const dislikeCount = dislikeButton.querySelector('.stat-count');
                
                if (dislikeIcon && dislikeCount) {
                    if (result.is_disliked) {
                        dislikeIcon.textContent = '💥';
                        dislikeButton.classList.add('active');
                        dislikeButton.style.background = 'rgba(239, 68, 68, 0.8)';
                    } else {
                        dislikeIcon.textContent = '💔';
                        dislikeButton.classList.remove('active');
                        dislikeButton.style.background = 'rgba(0, 0, 0, 0.7)';
                    }
                    
                    dislikeCount.textContent = formatCount(result.dislikes);
                }
            }
        }
    } catch (error) {
        console.error('Ошибка при переключении лайка:', error);
    } finally {
        setTimeout(() => {
            button.disabled = false;
        }, 500);
    }
}

async function toggleDislike(button) {
    if (!button || !button.dataset) {
        console.error('Некорректная кнопка дизлайка');
        return;
    }

    const postId = parseInt(button.dataset.postId);
    
    if (!postId || postId < 1) {
        console.error('Некорректный ID поста');
        return;
    }
    
    if (button.disabled) {
        return;
    }
    
    button.disabled = true;
    
    try {
        const result = await sendRequest('/toggle-dislike/', {
            post_id: postId
        });
        
        if (result && result.success) {
            const icon = button.querySelector('.stat-icon');
            const count = button.querySelector('.stat-count');
            
            if (!icon || !count) {
                console.error('Не найдены элементы кнопки дизлайка');
                return;
            }
            
            if (result.is_disliked) {
                icon.textContent = '💥';
                button.classList.add('active');
                button.style.background = 'rgba(239, 68, 68, 0.8)';
            } else {
                icon.textContent = '💔';
                button.classList.remove('active');
                button.style.background = 'rgba(0, 0, 0, 0.7)';
            }
            
            count.textContent = formatCount(result.dislikes);
            
            const likeButton = document.querySelector('.stat-item.like');
            if (likeButton) {
                const likeIcon = likeButton.querySelector('.stat-icon');
                const likeCount = likeButton.querySelector('.stat-count');
                
                if (likeIcon && likeCount) {
                    if (result.is_liked) {
                        likeIcon.textContent = '💖';
                        likeButton.classList.add('active');
                        likeButton.style.background = 'rgba(34, 197, 94, 0.8)';
                    } else {
                        likeIcon.textContent = '❤️';
                        likeButton.classList.remove('active');
                        likeButton.style.background = 'rgba(0, 0, 0, 0.7)';
                    }
                    
                    likeCount.textContent = formatCount(result.likes);
                }
            }
        }
    } catch (error) {
        console.error('Ошибка при переключении дизлайка:', error);
    } finally {
        setTimeout(() => {
            button.disabled = false;
        }, 500);
    }
}


async function incrementViews(postId) {
    const validatedPostId = parseInt(postId);
    
    if (!validatedPostId || validatedPostId < 1) {
        console.error('Некорректный ID поста для просмотров');
        return;
    }
    
    try {
        const result = await sendRequest('/increment-views/', {
            post_id: validatedPostId
        });
        
        if (result && result.success) {
            const viewsElement = document.querySelector('.stat-item.views .stat-count');
            if (viewsElement) {
                viewsElement.textContent = formatCount(result.views);
            }
            
            if (result.new_view) {
                console.log('Новый просмотр зарегистрирован');
            }
        }
    } catch (error) {
        console.error('Ошибка при увеличении просмотров:', error);
    }
}

async function addComment(postId, content, parentId = null) {
    const validatedPostId = parseInt(postId);
    
    if (!validatedPostId || validatedPostId < 1) {
        console.error('Некорректный ID поста для комментария');
        return false;
    }

    if (!content || content.trim().length === 0) {
        alert('Комментарий не может быть пустым');
        return false;
    }

    try {
        const requestData = {
            post_id: validatedPostId,
            content: content.trim()
        };

        if (parentId) {
            requestData.parent_comment_id = parseInt(parentId);
        }

        const result = await sendRequest('/add_comment/', requestData);
        
        if (result && result.success) {
            const commentsButton = document.querySelector('.stat-item.comments');
            if (commentsButton) {
                await toggleComments(commentsButton);
            }
            return true;
        } else {
            alert(result.error || 'Ошибка при добавлении комментария');
            return false;
        }
    } catch (error) {
        console.error('Ошибка при добавлении комментария:', error);
        return false;
    }
}

function toggleSearchByTag(button) {
    if (!button) {
        console.error('Кнопка тега не найдена');
        return;
    }
    
    const tagNameElement = button.querySelector('.tag-name');
    if (!tagNameElement) {
        console.error('Название тега не найдено');
        return;
    }
    
    const tagName = tagNameElement.textContent.trim();
    
    if (!tagName || tagName.length > 100) {
        console.error('Некорректное название тега');
        return;
    }
    
    const encodedTag = encodeURIComponent(tagName);
    alert(`Поиск по тегу: ${tagName} (пока недоступно)`);
    
}

document.addEventListener('DOMContentLoaded', function() {
    const mainContent = document.querySelector('.main-content');
    if (!mainContent) {
        console.error('Основной контент не найден');
        return;
    }
    

    const userReaction = mainContent.dataset.userReaction;
    
    if (userReaction === 'like') {
        const likeButton = document.querySelector('.stat-item.like');
        if (likeButton) {
            const icon = likeButton.querySelector('.stat-icon');
            if (icon) {
                icon.textContent = '💖';
                likeButton.classList.add('active');
                likeButton.style.background = 'rgba(34, 197, 94, 0.8)';
            }
        }
    } else if (userReaction === 'dislike') {
        const dislikeButton = document.querySelector('.stat-item.dislike');
        if (dislikeButton) {
            const icon = dislikeButton.querySelector('.stat-icon');
            if (icon) {
                icon.textContent = '💥';
                dislikeButton.classList.add('active');
                dislikeButton.style.background = 'rgba(239, 68, 68, 0.8)';
            }
        }
    }
    

    const commentsSection = document.querySelector('.comments-insertion');
    if (commentsSection) {
        commentsSection.style.display = 'none';
    }
});


window.sendRequest = sendRequest;
window.toggleLike = toggleLike;
window.toggleDislike = toggleDislike;
window.addComment = addComment;
window.toggleSearchByTag = toggleSearchByTag;
window.incrementViews = incrementViews;